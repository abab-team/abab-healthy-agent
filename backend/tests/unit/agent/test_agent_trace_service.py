from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_phase07a_trace.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")

from app.agent import service  # noqa: E402
from app.agent.enums import AgentSafetyLevel, AgentTraceStatus, AgentWorkflowName  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402


class AgentTraceServiceTestCase(unittest.TestCase):
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

    def test_start_trace_creates_trace(self) -> None:
        trace = service.start_trace(
            self.db,
            request_id="trace-start",
            workflow_name=AgentWorkflowName.CHAT_WORKFLOW,
            current_user_id=self.actor_user_id,
            target_user_id=self.target_user_id,
            raw_input_summary="short excerpt",
        )

        self.assertEqual(trace.status, AgentTraceStatus.RUNNING)
        self.assertEqual(trace.request_id, "trace-start")
        self.assertEqual(trace.raw_input_summary, "short excerpt")

    def test_complete_trace_marks_success(self) -> None:
        trace = self._start_trace("trace-complete")

        updated = service.complete_trace(self.db, trace.id, final_output_summary="done")

        self.assertEqual(updated.status, AgentTraceStatus.SUCCESS)
        self.assertEqual(updated.final_output_summary, "done")
        self.assertIsNotNone(updated.ended_at)

    def test_fail_trace_marks_failed(self) -> None:
        trace = self._start_trace("trace-failed")

        updated = service.fail_trace(
            self.db,
            trace.id,
            error_type="UnitError",
            error_message="safe failure",
            final_output_summary="failed",
        )

        self.assertEqual(updated.status, AgentTraceStatus.FAILED)
        self.assertEqual(updated.error_type, "UnitError")
        self.assertEqual(updated.error_message, "safe failure")

    def test_record_safety_check_writes_check(self) -> None:
        check = service.record_safety_check(
            self.db,
            request_id="safety-check",
            workflow_name=AgentWorkflowName.CHAT_WORKFLOW,
            safety_level=AgentSafetyLevel.CAUTION,
            passed=True,
            safety_flags=["medical_boundary_caution"],
            input_risk_summary="boundary only",
        )

        checks = service.list_safety_checks(self.db, request_id="safety-check")
        self.assertEqual(check.id, checks[0].id)
        self.assertEqual(check.safety_level, AgentSafetyLevel.CAUTION)
        self.assertEqual(check.safety_flags, ["medical_boundary_caution"])

    def _start_trace(self, request_id: str):
        return service.start_trace(
            self.db,
            request_id=request_id,
            workflow_name=AgentWorkflowName.CHAT_WORKFLOW,
            current_user_id=self.actor_user_id,
            target_user_id=self.target_user_id,
        )


if __name__ == "__main__":
    unittest.main()
