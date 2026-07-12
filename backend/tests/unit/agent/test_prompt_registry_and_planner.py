from __future__ import annotations

import unittest
from datetime import date

from app.agent.answer_composer import LLMAnswerComposer
from app.agent.chat.schemas import HealthQueryIntent
from app.agent.planner import LLMPlannerService, validate_llm_plan
from app.agent.prompts import PromptRenderError, get_prompt_registry
from app.core.config import Settings
from app.llm.schemas import LLMResponse


class StaticLLMClient:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls = 0

    def generate_text(self, **kwargs) -> LLMResponse:
        self.calls += 1
        return LLMResponse(
            content=self.content,
            provider="unit-test",
            model="unit-test-model",
            is_mock=True,
            finish_reason="unit-test",
        )


class PromptRegistryAndPlannerTestCase(unittest.TestCase):
    def test_prompt_registry_loads_versioned_planner_prompt(self) -> None:
        registry = get_prompt_registry()
        prompt = registry.get_prompt("health_query_planner", version="v1")

        rendered = prompt.render(
            {
                "user_message": "pressure readings",
                "recent_session_context_summary": "",
                "safe_memory_summary": "",
                "allowed_intents": prompt.allowed_intents,
                "allowed_metric_types": ("blood_pressure",),
                "allowed_member_scopes": ("self",),
                "allowed_time_ranges": ("last_7_days",),
            }
        )

        self.assertEqual(prompt.version, "v1")
        self.assertIn("Return JSON only", rendered)
        self.assertIn("query_blood_pressure", rendered)

    def test_valid_llm_plan_maps_to_backend_tool(self) -> None:
        result = validate_llm_plan(
            {
                "intent": "query_blood_pressure",
                "member_scope": "self",
                "metric_type": "blood_pressure",
                "time_range": "last_30_days",
                "aggregation": "summary",
                "confidence": 0.91,
                "needs_clarification": False,
            },
            settings=Settings(LLM_PLANNER_CONFIDENCE_THRESHOLD=0.75),
            reference_date=date(2026, 7, 9),
        )

        self.assertTrue(result.accepted)
        self.assertEqual(result.plan.intent, HealthQueryIntent.QUERY_BLOOD_PRESSURE)
        self.assertEqual(result.plan.tool_name, "health_data.blood_pressure.summary")
        self.assertEqual(result.plan.tool_input, {"days": 30})

    def test_prompt_render_requires_explicit_variables(self) -> None:
        prompt = get_prompt_registry().get_prompt("health_query_planner", version="v1")

        with self.assertRaises(PromptRenderError):
            prompt.render({"user_message": "hello"})

    def test_llm_plan_rejects_invalid_intent_and_forbidden_tool_keys(self) -> None:
        invalid_intent = validate_llm_plan(
            {
                "intent": "diagnose_user",
                "member_scope": "self",
                "time_range": "last_7_days",
                "confidence": 0.99,
                "needs_clarification": False,
            },
            settings=Settings(),
        )
        with_tool_name = validate_llm_plan(
            {
                "intent": "query_alerts",
                "member_scope": "self",
                "time_range": "last_7_days",
                "confidence": 0.99,
                "needs_clarification": False,
                "tool_name": "alerts.query",
            },
            settings=Settings(),
        )

        self.assertFalse(invalid_intent.accepted)
        self.assertEqual(invalid_intent.reason_code, "llm_plan_invalid_intent")
        self.assertFalse(with_tool_name.accepted)
        self.assertEqual(with_tool_name.reason_code, "llm_plan_forbidden_keys")

    def test_low_confidence_plan_requires_clarification(self) -> None:
        result = validate_llm_plan(
            {
                "intent": "query_metrics",
                "member_scope": "self",
                "metric_type": "sleep_duration",
                "time_range": "last_7_days",
                "aggregation": "summary",
                "confidence": 0.2,
                "needs_clarification": False,
            },
            settings=Settings(LLM_PLANNER_CONFIDENCE_THRESHOLD=0.75),
        )

        self.assertFalse(result.accepted)
        self.assertTrue(result.plan.needs_clarification)
        self.assertIsNone(result.plan.tool_name)

    def test_llm_planner_service_uses_prompt_and_validates_json(self) -> None:
        client = StaticLLMClient(
            '{"intent":"query_documents","member_scope":"self","time_range":"last_7_days",'
            '"aggregation":"summary","confidence":0.88,"needs_clarification":false}'
        )
        service = LLMPlannerService(
            settings=Settings(LLM_PLANNER_ENABLED=True, LLM_ENABLED=True),
            llm_client=client,
        )

        result = service.plan(user_message="Which files did I upload?", reference_date=date(2026, 7, 9))

        self.assertTrue(result.accepted)
        self.assertTrue(result.llm_used)
        self.assertEqual(client.calls, 1)
        self.assertEqual(result.plan.tool_name, "documents.query")

    def test_answer_composer_falls_back_when_llm_output_is_unsafe(self) -> None:
        client = StaticLLMClient("You should take 2 pills and no need to see a doctor.")
        composer = LLMAnswerComposer(
            settings=Settings(LLM_ANSWER_COMPOSER_ENABLED=True, LLM_ENABLED=True),
            llm_client=client,
        )

        result = composer.compose(
            safe_tool_result_summary="count=1",
            coverage_note="based on system records",
            user_question_excerpt="what should I do",
            fallback_answer="Based on system records only. This does not replace a doctor.",
        )

        self.assertTrue(result.llm_used)
        self.assertTrue(result.fallback_used)
        self.assertIn("system records", result.answer)

    def test_answer_composer_falls_back_when_llm_output_is_not_chinese(self) -> None:
        client = StaticLLMClient("Here is a safe summary from system records.")
        composer = LLMAnswerComposer(
            settings=Settings(LLM_ANSWER_COMPOSER_ENABLED=True, LLM_ENABLED=True),
            llm_client=client,
        )

        result = composer.compose(
            safe_tool_result_summary="count=1",
            coverage_note="\u4ec5\u57fa\u4e8e\u7cfb\u7edf\u8bb0\u5f55",
            user_question_excerpt="\u67e5\u8be2\u8840\u538b",
            fallback_answer="\u7cfb\u7edf\u5185\u6709 1 \u6761\u8840\u538b\u8bb0\u5f55\u3002",
        )

        self.assertTrue(result.llm_used)
        self.assertTrue(result.fallback_used)
        self.assertEqual(result.fallback_reason, "output_not_chinese")
        self.assertIn("\u8840\u538b", result.answer)


if __name__ == "__main__":
    unittest.main()
