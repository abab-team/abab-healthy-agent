from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_phase07d_executor.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")

from app.agent import service  # noqa: E402
from app.agent.enums import AgentToolCallStatus, AgentWorkflowName  # noqa: E402
from app.agent.schemas import AgentToolMetadata, ToolExecutionRequest  # noqa: E402
from app.agent.tool_executor import AgentToolExecutor  # noqa: E402
from app.agent.tool_registry import AgentToolRegistry  # noqa: E402
from app.agent.tools.base import AgentTool  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402


class AgentToolExecutorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        engine.dispose()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        self.actor_user_id = uuid4()
        self.target_user_id = uuid4()
        self.trace = service.start_trace(
            self.db,
            request_id=f"executor-{uuid4()}",
            workflow_name=AgentWorkflowName.CHAT_WORKFLOW,
            current_user_id=self.actor_user_id,
            target_user_id=self.target_user_id,
        )
        self.permission_checker = FakePermissionChecker()

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()
        engine.dispose()

    def test_system_noop_tool_executes_successfully(self) -> None:
        tool = FakeTool(system_metadata("safe_echo"))
        executor = self._executor(tool)

        result = executor.execute(self.db, self._request("safe_echo", {"message": "hello"}))

        self.assertEqual(result.status, "completed")
        self.assertFalse(result.blocked)
        self.assertEqual(result.output_data, {"ok": True, "message": "safe response"})
        self.assertEqual(tool.execute_count, 1)

    def test_success_creates_completed_tool_call(self) -> None:
        executor = self._executor(FakeTool(system_metadata("safe_echo")))

        result = executor.execute(self.db, self._request("safe_echo", {"raw_text": "long health note"}))
        calls = service.list_tool_calls(self.db, trace_id=self.trace.id)

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].id, result.tool_call_id)
        self.assertEqual(calls[0].status, AgentToolCallStatus.SUCCESS)
        self.assertIn("raw_text", calls[0].input_summary)

    def test_disabled_tool_does_not_execute(self) -> None:
        tool = FakeTool(system_metadata("disabled_tool", enabled=False))
        executor = self._executor(tool)

        result = executor.execute(self.db, self._request("disabled_tool"))

        self.assertTrue(result.blocked)
        self.assertEqual(result.error_code, "tool_disabled")
        self.assertEqual(tool.execute_count, 0)
        self.assertEqual(service.list_tool_calls(self.db, trace_id=self.trace.id)[0].status, AgentToolCallStatus.BLOCKED_BY_REGISTRY)

    def test_unregistered_tool_returns_safe_failure(self) -> None:
        executor = AgentToolExecutor(AgentToolRegistry(), permission_checker=self.permission_checker)

        result = executor.execute(self.db, self._request("missing_tool"))

        self.assertTrue(result.blocked)
        self.assertEqual(result.error_code, "tool_not_found")
        self.assertNotIn("Traceback", result.message)
        self.assertEqual(service.list_tool_calls(self.db, trace_id=self.trace.id)[0].status, AgentToolCallStatus.BLOCKED_BY_REGISTRY)

    def test_declared_confirmation_blocks_without_confirmation(self) -> None:
        tool = FakeTool(system_metadata("confirm_tool", requires_confirmation=True))
        executor = self._executor(tool)

        result = executor.execute(self.db, self._request("confirm_tool", confirmed=False))

        self.assertTrue(result.blocked)
        self.assertTrue(result.requires_confirmation)
        self.assertEqual(result.error_code, "confirmation_required")
        self.assertEqual(tool.execute_count, 0)

    def test_declared_confirmation_executes_when_confirmed(self) -> None:
        tool = FakeTool(system_metadata("confirm_tool", requires_confirmation=True))
        executor = self._executor(tool)

        result = executor.execute(self.db, self._request("confirm_tool", confirmed=True))

        self.assertFalse(result.blocked)
        self.assertEqual(tool.execute_count, 1)

    def test_write_tool_blocks_without_confirmation(self) -> None:
        tool = FakeTool(permission_metadata("write_tool", access_mode="write", requires_confirmation=True))
        executor = self._executor(tool)

        result = executor.execute(self.db, self._request("write_tool", confirmed=False))

        self.assertTrue(result.blocked)
        self.assertEqual(result.error_code, "confirmation_required")
        self.assertEqual(tool.execute_count, 0)

    def test_high_risk_tool_blocks_without_confirmation(self) -> None:
        tool = FakeTool(permission_metadata("risk_tool", risk_level="high", requires_confirmation=True))
        executor = self._executor(tool)

        result = executor.execute(self.db, self._request("risk_tool", confirmed=False))

        self.assertTrue(result.blocked)
        self.assertEqual(result.error_code, "confirmation_required")
        self.assertEqual(tool.execute_count, 0)

    def test_permission_denied_does_not_execute_tool(self) -> None:
        checker = FakePermissionChecker(allowed=False)
        tool = FakeTool(permission_metadata("family_read_tool"))
        executor = self._executor(tool, permission_checker=checker)

        result = executor.execute(self.db, self._request("family_read_tool", family_id=uuid4()))

        self.assertTrue(result.blocked)
        self.assertEqual(result.error_code, "permission_denied")
        self.assertEqual(tool.execute_count, 0)

    def test_permission_denied_records_blocked_tool_call(self) -> None:
        checker = FakePermissionChecker(allowed=False)
        executor = self._executor(FakeTool(permission_metadata("family_read_tool")), permission_checker=checker)

        executor.execute(self.db, self._request("family_read_tool", family_id=uuid4()))
        call = service.list_tool_calls(self.db, trace_id=self.trace.id)[0]

        self.assertEqual(call.status, AgentToolCallStatus.BLOCKED_BY_PERMISSION)
        self.assertTrue(call.permission_checked)
        self.assertFalse(call.permission_result["allowed"])

    def test_permission_denied_does_not_return_target_health_data(self) -> None:
        checker = FakePermissionChecker(allowed=False)
        executor = self._executor(FakeTool(permission_metadata("family_read_tool")), permission_checker=checker)

        result = executor.execute(self.db, self._request("family_read_tool", {"secret": "target symptom"}, family_id=uuid4()))

        self.assertNotIn("target symptom", result.message)
        self.assertIsNone(result.output_data)

    def test_missing_family_context_blocks_cross_user_permission_tool(self) -> None:
        executor = self._executor(FakeTool(permission_metadata("family_read_tool")))

        result = executor.execute(self.db, self._request("family_read_tool", family_id=None))

        self.assertEqual(result.error_code, "permission_denied")
        self.assertEqual(self.permission_checker.call_count, 0)

    def test_tool_exception_marks_failed(self) -> None:
        tool = FakeTool(system_metadata("boom_tool"), raises=True)
        executor = self._executor(tool)

        result = executor.execute(self.db, self._request("boom_tool"))
        call = service.list_tool_calls(self.db, trace_id=self.trace.id)[0]

        self.assertEqual(result.status, "failed")
        self.assertEqual(call.status, AgentToolCallStatus.FAILED)
        self.assertNotIn("boom", result.message)

    def test_executor_does_not_import_llm(self) -> None:
        sys.modules.pop("app.agent.llm_client", None)
        executor = self._executor(FakeTool(system_metadata("safe_echo")))

        executor.execute(self.db, self._request("safe_echo"))

        self.assertNotIn("app.agent.llm_client", sys.modules)

    def test_executor_does_not_read_or_write_health_business_data(self) -> None:
        tool = FakeTool(system_metadata("safe_echo"))
        executor = self._executor(tool)

        executor.execute(self.db, self._request("safe_echo"))

        self.assertFalse(tool.read_health_data)
        self.assertFalse(tool.write_health_data)

    def test_executor_does_not_create_real_business_records(self) -> None:
        executor = self._executor(FakeTool(system_metadata("safe_echo")))

        executor.execute(self.db, self._request("safe_echo"))

        self.assertEqual(len(service.list_tool_calls(self.db, trace_id=self.trace.id)), 1)

    def test_list_tool_calls_by_trace_returns_records(self) -> None:
        executor = self._executor(FakeTool(system_metadata("safe_echo")))

        first = executor.execute(self.db, self._request("safe_echo"))
        second = executor.execute(self.db, self._request("safe_echo"))
        calls = service.list_tool_calls(self.db, trace_id=self.trace.id)

        self.assertEqual([call.id for call in calls], [first.tool_call_id, second.tool_call_id])

    def test_output_summary_removes_unsafe_medical_text(self) -> None:
        tool = FakeTool(system_metadata("unsafe_echo"), output={"message": "The diagnosis is flu. Take 2 pills."})
        executor = self._executor(tool)

        executor.execute(self.db, self._request("unsafe_echo"))
        call = service.list_tool_calls(self.db, trace_id=self.trace.id)[0]
        summary_text = str(call.output_summary)

        self.assertIn("unsafe_medical_content_removed", summary_text)
        self.assertNotIn("diagnosis is flu", summary_text.lower())
        self.assertNotIn("take 2 pills", summary_text.lower())

    def test_safety_level_blocks_execution(self) -> None:
        tool = FakeTool(system_metadata("safe_echo"))
        executor = self._executor(tool)

        result = executor.execute(self.db, self._request("safe_echo", safety_level="blocked"))

        self.assertEqual(result.error_code, "safety_blocked")
        self.assertEqual(tool.execute_count, 0)

    def _executor(self, tool: AgentTool, *, permission_checker: FakePermissionChecker | None = None) -> AgentToolExecutor:
        registry = AgentToolRegistry()
        registry.register(tool)
        return AgentToolExecutor(registry, permission_checker=permission_checker or self.permission_checker)

    def _request(
        self,
        tool_name: str,
        input_data: dict | None = None,
        *,
        confirmed: bool = False,
        family_id=None,
        safety_level: str | None = None,
    ) -> ToolExecutionRequest:
        return ToolExecutionRequest(
            trace_id=self.trace.id,
            tool_name=tool_name,
            actor_user_id=self.actor_user_id,
            target_user_id=self.target_user_id,
            family_id=family_id,
            input_data=input_data or {"message": "hello"},
            confirmed=confirmed,
            safety_level=safety_level,
            reason="unit-test",
        )


class FakeTool(AgentTool):
    def __init__(self, metadata: AgentToolMetadata, *, output: dict | None = None, raises: bool = False) -> None:
        self.metadata = metadata
        self.output = output or {"ok": True, "message": "safe response"}
        self.raises = raises
        self.execute_count = 0
        self.read_health_data = False
        self.write_health_data = False

    def execute(self, payload: dict) -> dict:
        self.execute_count += 1
        if self.raises:
            raise RuntimeError("boom")
        return dict(self.output)


class FakePermissionChecker:
    def __init__(self, *, allowed: bool = True) -> None:
        self.allowed = allowed
        self.call_count = 0

    def __call__(self, db, **kwargs):
        self.call_count += 1
        return FakePermissionResult(
            allowed=self.allowed,
            permission_type=kwargs.get("permission_type"),
            action=kwargs.get("action"),
            reason="allowed" if self.allowed else "permission_denied",
        )


class FakePermissionResult:
    def __init__(self, *, allowed: bool, permission_type: str, action: str, reason: str) -> None:
        self.allowed = allowed
        self.permission_type = permission_type
        self.action = action
        self.reason = reason
        self.visibility_scope = "unit-test"
        self.safe_message = "safe permission message"


def system_metadata(name: str, *, enabled: bool = True, requires_confirmation: bool = False) -> AgentToolMetadata:
    return AgentToolMetadata(
        name=name,
        description="Unit-test system tool.",
        category="system",
        access_mode="read",
        risk_level="low",
        requires_confirmation=requires_confirmation,
        enabled=enabled,
    )


def permission_metadata(
    name: str,
    *,
    access_mode: str = "read",
    risk_level: str = "medium",
    requires_confirmation: bool = False,
) -> AgentToolMetadata:
    return AgentToolMetadata(
        name=name,
        description="Unit-test permission tool.",
        category="health_data",
        access_mode=access_mode,
        risk_level=risk_level,
        required_permission_type="metrics",
        required_permission_action="view",
        requires_confirmation=requires_confirmation,
    )


if __name__ == "__main__":
    unittest.main()
