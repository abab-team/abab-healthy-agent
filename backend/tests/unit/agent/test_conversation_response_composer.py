from __future__ import annotations

import unittest

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agent.conversation_v2.response_composer import ConversationResponseComposer, build_safe_conversation_facts
from app.core.config import Settings
from app.llm.schemas import LLMResponse


class ConversationResponseComposerTestCase(unittest.TestCase):
    def _safe_state(self) -> dict:
        return {
            "plan_summary": {
                "intent": "query_blood_pressure",
                "member_label": "你",
                "time_range_label": "最近7天",
                "days": 7,
            },
            "resolved_member_context": {"member": "你", "allowed": True},
            "tool_execution_results": [
                {
                    "tool": "health_data.blood_pressure.summary",
                    "status": "completed",
                    "blocked": False,
                    "count": 3,
                    "empty": False,
                    "summary": {
                        "latest_systolic": 118,
                        "latest_diastolic": 76,
                        "avg_systolic": 124,
                        "avg_diastolic": 81,
                    },
                }
            ],
        }

    def test_safe_fact_builder_uses_allowlisted_summary_not_raw_tool_message(self) -> None:
        messages = [
            HumanMessage(content="查询我的血压"),
            ToolMessage(
                content='{"tool":"health_data.blood_pressure.summary","summary":{"latest_systolic":118,"latest_diastolic":76},"file_path":"C:/private.pdf","raw_extracted_text":"private note","token":"secret"}',
                tool_call_id="call-1",
            ),
        ]

        facts = build_safe_conversation_facts(state=self._safe_state(), messages=messages)
        payload = str(facts.as_prompt_payload())

        self.assertIn("118/76", payload)
        self.assertNotIn("private.pdf", payload)
        self.assertNotIn("private note", payload)
        self.assertNotIn("secret", payload)

    def test_composer_uses_safe_facts_and_history_without_raw_tool_content(self) -> None:
        client = _RecordingClient("我看了一下你最近的血压记录。最近共记录3次，最新一次是118/76 mmHg，平均约124/81 mmHg。可以继续看看30天变化。")
        composer = ConversationResponseComposer(
            settings=Settings(LLM_ENABLED=True, LLM_CHAT_ENABLED=True),
            llm_client=client,
        )
        history = [
            HumanMessage(content="之前聊过睡眠"),
            AIMessage(content="好的，我们继续。"),
            HumanMessage(content="查询我的血压"),
            ToolMessage(content='{"raw_extracted_text":"never send","file_path":"C:/private.pdf"}', tool_call_id="call-1"),
        ]
        facts = build_safe_conversation_facts(state=self._safe_state(), messages=history)

        result = composer.compose(
            history=history,
            user_question="查询我的血压",
            facts=facts,
            fallback_answer="fallback",
        )
        prompt = "\n".join(message.content for message in client.calls[0])
        system_prompt = client.calls[0][0].content

        self.assertTrue(result.llm_used)
        self.assertFalse(result.fallback_used)
        self.assertIn("118/76", result.content)
        self.assertIn("健康小伙伴", system_prompt)
        self.assertIn("温柔、细心、自然", system_prompt)
        self.assertNotIn("never send", prompt)
        self.assertNotIn("private.pdf", prompt)
        self.assertNotIn("raw_extracted_text", prompt)

    def test_unsafe_output_uses_legacy_fallback(self) -> None:
        composer = ConversationResponseComposer(
            settings=Settings(LLM_ENABLED=True, LLM_CHAT_ENABLED=True),
            llm_client=_RecordingClient("诊断是高血压，请停药。"),
        )
        facts = build_safe_conversation_facts(state=self._safe_state(), messages=[HumanMessage(content="查询血压")])

        result = composer.compose(
            history=[HumanMessage(content="查询血压")],
            user_question="查询血压",
            facts=facts,
            fallback_answer="安全降级回复",
        )

        self.assertEqual(result.content, "安全降级回复")
        self.assertTrue(result.fallback_used)
        self.assertEqual(result.fallback_reason, "output_safety_blocked")

    def test_assurance_only_output_uses_legacy_fallback(self) -> None:
        composer = ConversationResponseComposer(
            settings=Settings(LLM_ENABLED=True, LLM_CHAT_ENABLED=True),
            llm_client=_RecordingClient("这份记录说明你可以放心。"),
        )
        facts = build_safe_conversation_facts(state=self._safe_state(), messages=[HumanMessage(content="查询血压")])

        result = composer.compose(
            history=[HumanMessage(content="查询血压")],
            user_question="查询血压",
            facts=facts,
            fallback_answer="安全降级回复",
        )

        self.assertEqual(result.content, "安全降级回复")
        self.assertEqual(result.fallback_reason, "assurance_only_output")

    def test_assurance_sentence_is_removed_without_discarding_grounded_facts(self) -> None:
        composer = ConversationResponseComposer(
            settings=Settings(LLM_ENABLED=True, LLM_CHAT_ENABLED=True),
            llm_client=_RecordingClient("整体挺平稳。最近一次血压是118/76 mmHg，可以继续查看近期变化。"),
        )
        facts = build_safe_conversation_facts(state=self._safe_state(), messages=[HumanMessage(content="查询血压")])

        result = composer.compose(
            history=[HumanMessage(content="查询血压")],
            user_question="查询血压",
            facts=facts,
            fallback_answer="安全降级回复",
        )

        self.assertNotIn("整体挺平稳", result.content)
        self.assertIn("118/76 mmHg", result.content)
        self.assertFalse(result.fallback_used)

    def test_diagnostic_reference_sentence_is_removed_but_general_context_remains(self) -> None:
        composer = ConversationResponseComposer(
            settings=Settings(LLM_ENABLED=True, LLM_CHAT_ENABLED=True),
            llm_client=_RecordingClient(
                "最近一次是118/76 mmHg。常见诊断界限会因指南不同而变化。"
                "单次记录不能代表长期情况，可以继续查看趋势。"
            ),
        )
        facts = build_safe_conversation_facts(state=self._safe_state(), messages=[HumanMessage(content="查询血压")])

        result = composer.compose(
            history=[HumanMessage(content="查询血压")],
            user_question="这个数值怎么样",
            facts=facts,
            fallback_answer="安全降级回复",
        )

        self.assertNotIn("诊断界限", result.content)
        self.assertIn("118/76 mmHg", result.content)
        self.assertIn("单次记录", result.content)
        self.assertFalse(result.fallback_used)

    def test_common_reference_range_explanation_is_allowed(self) -> None:
        composer = ConversationResponseComposer(
            settings=Settings(LLM_ENABLED=True, LLM_CHAT_ENABLED=True),
            llm_client=_RecordingClient("118/76 mmHg 属于正常范围。"),
        )
        facts = build_safe_conversation_facts(state=self._safe_state(), messages=[HumanMessage(content="查询血压")])

        result = composer.compose(
            history=[HumanMessage(content="查询血压")],
            user_question="查询血压",
            facts=facts,
            fallback_answer="安全降级回复",
        )

        self.assertIn("118/76 mmHg", result.content)
        self.assertIn("正常范围", result.content)
        self.assertFalse(result.fallback_used)

    def test_boundary_is_only_required_for_first_health_reply_in_topic(self) -> None:
        first = build_safe_conversation_facts(state=self._safe_state(), messages=[HumanMessage(content="查询血压")])
        continued = build_safe_conversation_facts(
            state=self._safe_state(),
            messages=[AIMessage(content="内容基于系统内已有记录整理，不替代医生判断。"), HumanMessage(content="这个数值怎么样")],
        )

        self.assertTrue(first.boundary_required)
        self.assertFalse(continued.boundary_required)

    def test_family_overview_fact_package_keeps_member_and_multiple_safe_sections(self) -> None:
        state = {
            "plan_summary": {"intent": "query_daily_status", "member_label": "爸爸", "time_range_label": "最近7天", "days": 7},
            "resolved_member_context": {"member": "爸爸", "allowed": True},
            "tool_execution_results": [
                {"tool": "health_data.metrics.recent", "status": "completed", "blocked": False, "count": 4, "empty": False, "summary": {}},
                {"tool": "health_data.blood_pressure.summary", "status": "completed", "blocked": False, "count": 2, "empty": False, "summary": {"latest_systolic": 145, "latest_diastolic": 92}},
                {"tool": "health_record.symptoms.query", "status": "completed", "blocked": False, "count": 1, "empty": False, "summary": {}},
            ],
        }

        facts = build_safe_conversation_facts(state=state, messages=[HumanMessage(content="爸爸最近怎么样")])

        self.assertEqual(facts.subject, "爸爸")
        self.assertEqual(facts.topic, "health_overview")
        self.assertIn("最近整理到 4 条健康指标记录", facts.facts)
        self.assertIn("最近一次血压是 145/92 mmHg", facts.facts)
        self.assertIn("相关症状记录共有 1 条", facts.facts)

    def test_business_overview_aggregates_safe_sections_without_raw_tool_payloads(self) -> None:
        state = {
            "tool_execution_results": [
                {
                    "capability": "health_overview",
                    "subject_label": "爸爸",
                    "period": "7d",
                    "facts": {
                        "profile": {"available": True},
                        "blood_pressure": {"record_count": 2, "latest": "145/92 mmHg", "average": "142/90 mmHg"},
                        "metrics": {"record_count": 4},
                        "symptoms": {"record_count": 1},
                        "medical_events": {"record_count": 1},
                        "documents": {"record_count": 2},
                        "alerts": {"record_count": 1},
                    },
                    "unavailable_sections": [],
                    "safe_next_actions": [],
                }
            ]
        }

        facts = build_safe_conversation_facts(state=state, messages=[HumanMessage(content="爸爸最近怎么样")])

        self.assertEqual(facts.subject, "爸爸")
        self.assertEqual(facts.topic, "health_overview")
        self.assertIn("最近一次血压是 145/92 mmHg", facts.facts)
        self.assertIn("相关健康指标共有 4 条", facts.facts)
        self.assertIn("相关症状记录共有 1 条", facts.facts)
        self.assertIn("相关医疗资料共有 2 条", facts.facts)


class _RecordingClient:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls = []

    def chat(self, messages, **kwargs):  # noqa: ANN001, ANN003
        self.calls.append(messages)
        return LLMResponse(content=self.content, provider="test", model="test", is_mock=True)


if __name__ == "__main__":
    unittest.main()
