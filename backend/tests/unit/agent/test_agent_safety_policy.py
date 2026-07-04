from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_phase07c_safety.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")

from sqlalchemy import select  # noqa: E402

from app.agent import service  # noqa: E402
from app.agent.enums import AgentTraceStatus, AgentWorkflowName  # noqa: E402
from app.agent.models import AgentToolCall  # noqa: E402
from app.agent.runtime import AgentRuntime  # noqa: E402
from app.agent.safety import AgentSafetyPolicy, MAX_AGENT_USER_MESSAGE_LENGTH  # noqa: E402
from app.agent.schemas import AgentRunRequest, AgentWorkflowResult  # noqa: E402
from app.agent.workflows import AgentWorkflowRegistry, NoOpHealthAssistantWorkflow  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402


class AgentSafetyPolicyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = AgentSafetyPolicy()

    def test_empty_input_is_blocked(self) -> None:
        decision = self.policy.evaluate_input("   ")

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.reason_code, "empty_input")

    def test_too_long_input_is_blocked(self) -> None:
        decision = self.policy.evaluate_input("a" * (MAX_AGENT_USER_MESSAGE_LENGTH + 1))

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.reason_code, "input_too_long")

    def test_diagnosis_request_is_caution_without_diagnosis(self) -> None:
        decision = self.policy.evaluate_input("Can you diagnose what disease I have?")

        self.assertFalse(decision.blocked)
        self.assertEqual(decision.safety_level, "caution")
        self.assertNotIn("you have", decision.safe_message.lower())

    def test_chinese_diagnosis_request_is_caution(self) -> None:
        decision = self.policy.evaluate_input("请帮我诊断这是什么病")

        self.assertFalse(decision.blocked)
        self.assertEqual(decision.safety_level, "caution")

    def test_prescription_request_is_blocked(self) -> None:
        decision = self.policy.evaluate_input("What medicine should I take?")

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.category, "prescription_request")

    def test_chinese_prescription_request_is_blocked(self) -> None:
        decision = self.policy.evaluate_input("请给我开药")

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.category, "prescription_request")

    def test_dosage_request_is_blocked(self) -> None:
        decision = self.policy.evaluate_input("How many pills should I take?")

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.category, "dosage_request")

    def test_chinese_dosage_request_is_blocked(self) -> None:
        decision = self.policy.evaluate_input("这个药应该吃多少剂量")

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.category, "dosage_request")

    def test_stop_medication_request_is_blocked(self) -> None:
        decision = self.policy.evaluate_input("Can I stop medication today?")

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.category, "medication_change_request")

    def test_chinese_stop_medication_request_is_blocked(self) -> None:
        decision = self.policy.evaluate_input("我今天可以停药吗")

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.category, "medication_change_request")

    def test_emergency_keywords_are_emergency(self) -> None:
        decision = self.policy.evaluate_input("I have chest pain and difficulty breathing")

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.safety_level, "emergency")
        self.assertTrue(decision.requires_medical_attention)

    def test_chinese_emergency_keywords_are_emergency(self) -> None:
        decision = self.policy.evaluate_input("我现在胸痛并且呼吸困难")

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.safety_level, "emergency")
        self.assertTrue(decision.requires_medical_attention)

    def test_self_harm_expression_is_emergency(self) -> None:
        decision = self.policy.evaluate_input("I want to kill myself")

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.category, "self_harm")

    def test_chinese_self_harm_expression_is_emergency(self) -> None:
        decision = self.policy.evaluate_input("我不想活了")

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.category, "self_harm")

    def test_record_keeping_request_is_safe(self) -> None:
        decision = self.policy.evaluate_input("Please record my headache today")

        self.assertFalse(decision.blocked)
        self.assertEqual(decision.category, "record_keeping")

    def test_chinese_record_keeping_request_is_safe(self) -> None:
        decision = self.policy.evaluate_input("请记录我今天头疼")

        self.assertFalse(decision.blocked)
        self.assertEqual(decision.category, "record_keeping")

    def test_system_record_summary_request_is_safe(self) -> None:
        decision = self.policy.evaluate_input("Summarize recent system records")

        self.assertFalse(decision.blocked)
        self.assertEqual(decision.category, "health_summary")

    def test_output_diagnosis_is_blocked(self) -> None:
        decision = self.policy.evaluate_output("The diagnosis is hypertension.")

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.reason_code, "unsafe_medical_output")

    def test_output_dosage_advice_is_blocked(self) -> None:
        decision = self.policy.evaluate_output("Take 2 pills every morning.")

        self.assertTrue(decision.blocked)

    def test_output_certainty_claim_is_blocked(self) -> None:
        decision = self.policy.evaluate_output("No need to see a doctor. It is definitely fine.")

        self.assertTrue(decision.blocked)

    def test_safe_message_has_no_prescription_dosage_or_stop_medication_advice(self) -> None:
        decision = self.policy.evaluate_input("How much medicine should I take?")
        message = decision.safe_message.lower()

        self.assertNotIn("take 2", message)
        self.assertNotIn("mg", message)
        self.assertNotIn("stop your medication", message)

    def test_policy_does_not_import_llm(self) -> None:
        sys.modules.pop("app.agent.llm_client", None)

        self.policy.evaluate_input("hello")

        self.assertNotIn("app.agent.llm_client", sys.modules)

    def test_policy_does_not_import_db(self) -> None:
        sys.modules.pop("app.db.session", None)

        self.policy.evaluate_input("hello")

        self.assertNotIn("app.db.session", sys.modules)


class AgentSafetyRuntimeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        engine.dispose()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        self.actor_user_id = uuid4()
        self.target_user_id = uuid4()

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()
        engine.dispose()

    def test_runtime_blocked_input_does_not_execute_workflow(self) -> None:
        registry = AgentWorkflowRegistry()
        workflow = CountingWorkflow()
        registry.register(workflow)

        result = AgentRuntime(registry=registry).run(self.db, self._request("What medicine should I take?"))

        self.assertEqual(result.status, "blocked")
        self.assertTrue(result.blocked)
        self.assertEqual(workflow.run_count, 0)

    def test_runtime_caution_input_can_execute_noop_workflow(self) -> None:
        result = AgentRuntime().run(self.db, self._request("Can you diagnose this symptom?"))

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.safety_level, "caution")
        self.assertFalse(result.blocked)

    def test_runtime_unsafe_output_is_replaced(self) -> None:
        registry = AgentWorkflowRegistry()
        registry.register(UnsafeOutputWorkflow())

        result = AgentRuntime(registry=registry).run(self.db, self._request("hello"))

        self.assertEqual(result.status, "completed")
        self.assertTrue(result.blocked)
        self.assertNotIn("take 2 pills", (result.generated_content or "").lower())
        self.assertIn("replaced an unsafe response", result.generated_content or "")

    def test_safety_check_is_persisted(self) -> None:
        result = AgentRuntime().run(self.db, self._request("hello"))
        trace = service.get_trace(self.db, result.trace_id)

        checks = service.list_safety_checks(self.db, request_id=trace.request_id)

        self.assertGreaterEqual(len(checks), 2)

    def test_trace_does_not_remain_running_after_blocked_input(self) -> None:
        result = AgentRuntime().run(self.db, self._request("I have chest pain"))
        trace = service.get_trace(self.db, result.trace_id)

        self.assertEqual(trace.status, AgentTraceStatus.BLOCKED)

    def test_runtime_does_not_create_tool_calls(self) -> None:
        AgentRuntime().run(self.db, self._request("hello"))

        count = len(list(self.db.scalars(select(AgentToolCall.id))))
        self.assertEqual(count, 0)

    def _request(self, user_message: str) -> AgentRunRequest:
        return AgentRunRequest(
            actor_user_id=self.actor_user_id,
            target_user_id=self.target_user_id,
            family_id=None,
            workflow_type=AgentWorkflowName.CHAT_WORKFLOW,
            user_message=user_message,
            source="unit-test",
        )


class CountingWorkflow(NoOpHealthAssistantWorkflow):
    def __init__(self) -> None:
        self.run_count = 0

    def run(self, request: AgentRunRequest) -> AgentWorkflowResult:
        self.run_count += 1
        return super().run(request)


class UnsafeOutputWorkflow(NoOpHealthAssistantWorkflow):
    def run(self, request: AgentRunRequest) -> AgentWorkflowResult:
        content = "The diagnosis is flu. Take 2 pills and no need to see a doctor."
        return AgentWorkflowResult(message=content, generated_content=content, tool_calls_count=0)


if __name__ == "__main__":
    unittest.main()
