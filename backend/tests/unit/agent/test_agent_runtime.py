from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_phase07a_runtime.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")

from sqlalchemy import select  # noqa: E402

from app.agent import service  # noqa: E402
from app.agent.enums import AgentTraceStatus, AgentWorkflowName  # noqa: E402
from app.agent.models import AgentToolCall  # noqa: E402
from app.agent.runtime import AgentRuntime  # noqa: E402
from app.agent.schemas import AgentRunRequest, AgentWorkflowContext, AgentWorkflowResult  # noqa: E402
from app.agent.workflows import AgentWorkflowRegistry, NoOpHealthAssistantWorkflow  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402


class AgentRuntimeTestCase(unittest.TestCase):
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

    def test_chat_workflow_unknown_intent_returns_safe_message(self) -> None:
        result = AgentRuntime().run(self.db, self._request("hello"))

        self.assertEqual(result.status, "completed")
        self.assertFalse(result.blocked)
        self.assertEqual(result.tool_calls_count, 0)
        self.assertIn("系统内记录", result.generated_content or "")
        trace = service.get_trace(self.db, result.trace_id)
        self.assertEqual(trace.status, AgentTraceStatus.SUCCESS)

    def test_runtime_does_not_create_tool_calls(self) -> None:
        result = AgentRuntime().run(self.db, self._request("hello"))

        count = len(list(self.db.scalars(select(AgentToolCall.id))))
        self.assertEqual(result.tool_calls_count, 0)
        self.assertEqual(count, 0)

    def test_runtime_does_not_import_llm_client(self) -> None:
        sys.modules.pop("app.agent.llm_client", None)

        AgentRuntime().run(self.db, self._request("hello"))

        self.assertNotIn("app.agent.llm_client", sys.modules)

    def test_empty_user_message_is_blocked(self) -> None:
        result = AgentRuntime().run(self.db, self._request("   "))

        self.assertEqual(result.status, "blocked")
        self.assertTrue(result.blocked)
        trace = service.get_trace(self.db, result.trace_id)
        self.assertEqual(trace.status, AgentTraceStatus.BLOCKED)
        checks = service.list_safety_checks(self.db, request_id=trace.request_id)
        self.assertFalse(checks[0].passed)

    def test_too_long_user_message_is_blocked(self) -> None:
        result = AgentRuntime().run(self.db, self._request("a" * 2001))

        self.assertEqual(result.status, "blocked")
        self.assertTrue(result.blocked)
        self.assertIsNone(result.generated_content)

    def test_unregistered_workflow_returns_safe_error(self) -> None:
        result = AgentRuntime().run(self.db, self._request("hello", workflow_type=AgentWorkflowName.DAILY_REPORT_WORKFLOW))

        self.assertEqual(result.status, "failed")
        self.assertTrue(result.blocked)
        self.assertNotIn("Traceback", result.message)
        trace = service.get_trace(self.db, result.trace_id)
        self.assertEqual(trace.status, AgentTraceStatus.FAILED)

    def test_unknown_workflow_string_returns_safe_error(self) -> None:
        result = AgentRuntime().run(self.db, self._request("hello", workflow_type="unknown_workflow"))

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.workflow_type, "unknown_workflow")
        self.assertTrue(result.blocked)
        self.assertNotIn("Traceback", result.message)
        trace = service.get_trace(self.db, result.trace_id)
        self.assertEqual(trace.status, AgentTraceStatus.FAILED)

    def test_runtime_failure_marks_trace_failed(self) -> None:
        registry = AgentWorkflowRegistry()
        registry.register(FailingWorkflow())

        result = AgentRuntime(registry=registry).run(self.db, self._request("hello"))

        self.assertEqual(result.status, "failed")
        trace = service.get_trace(self.db, result.trace_id)
        self.assertEqual(trace.status, AgentTraceStatus.FAILED)
        self.assertEqual(trace.error_type, "RuntimeError")
        self.assertNotIn("boom", result.message)

    def test_medical_boundary_request_records_caution_without_advice(self) -> None:
        result = AgentRuntime().run(self.db, self._request("Can you diagnose me?"))

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.safety_level, "caution")
        generated = result.generated_content or ""
        self.assertNotIn("diagnosis is", generated.lower())
        self.assertNotIn("prescription", generated.lower())
        self.assertNotIn("dosage", generated.lower())

    def _request(self, user_message: str, *, workflow_type: AgentWorkflowName = AgentWorkflowName.CHAT_WORKFLOW) -> AgentRunRequest:
        return AgentRunRequest(
            actor_user_id=self.actor_user_id,
            target_user_id=self.target_user_id,
            family_id=None,
            workflow_type=workflow_type,
            user_message=user_message,
            source="unit-test",
        )


class FailingWorkflow(NoOpHealthAssistantWorkflow):
    def run(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
        raise RuntimeError("boom with stack-worthy details")


if __name__ == "__main__":
    unittest.main()
