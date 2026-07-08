from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from uuid import uuid4

TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_phase16_query_tools.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")

from app.agent import service as agent_service  # noqa: E402
from app.agent.enums import AgentWorkflowName  # noqa: E402
from app.agent.schemas import ToolExecutionRequest  # noqa: E402
from app.agent.tool_executor import AgentToolExecutor  # noqa: E402
from app.agent.tool_registry import AgentToolRegistry  # noqa: E402
from app.agent.tools import register_health_query_tools  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.modules.document_center import service as document_service  # noqa: E402
from app.modules.document_center.enums import DocumentType  # noqa: E402
from app.modules.family import service as family_service  # noqa: E402
from app.modules.health_data import service as health_data_service  # noqa: E402
from app.modules.health_record import service as health_record_service  # noqa: E402
from app.modules.identity import service as identity_service  # noqa: E402
from app.modules.permissions import service as permissions_service  # noqa: E402


QUERY_TOOL_NAMES = {
    "health_profile.get",
    "health_data.blood_pressure.summary",
    "health_record.symptoms.summary",
    "medical_timeline.followups.list",
    "alerts.active.list",
    "health_data.metric.summary",
    "health_data.metrics.recent",
    "health_record.symptoms.query",
    "medical_timeline.events.query",
    "documents.query",
    "alerts.query",
}


class HealthQueryToolsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        engine.dispose()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        suffix = uuid4().hex[:8]
        self.actor = identity_service.create_user(
            self.db,
            email=f"phase16.actor.{suffix}@example.com",
            phone=f"p16_actor_{suffix}",
            nickname="Actor",
        )
        self.target = identity_service.create_user(
            self.db,
            email=f"phase16.target.{suffix}@example.com",
            phone=f"p16_target_{suffix}",
            nickname="Target",
        )
        self.family = family_service.create_family_with_owner(
            self.db,
            owner_user_id=self.actor.id,
            family_name="Phase 16 Family",
            owner_display_name="Actor",
        )
        family_service.add_registered_member(
            self.db,
            family_id=self.family.id,
            user_id=self.target.id,
            relationship_label="member",
            display_name="Target",
        )
        permissions_service.create_default_permissions_for_member(
            self.db,
            family_id=self.family.id,
            user_id=self.target.id,
            share_all=True,
        )
        self.registry = register_health_query_tools(AgentToolRegistry())
        self.executor = AgentToolExecutor(self.registry)
        self.trace = agent_service.start_trace(
            self.db,
            request_id=f"query-tools-{uuid4()}",
            workflow_name=AgentWorkflowName.CHAT_WORKFLOW,
            current_user_id=self.actor.id,
            target_user_id=self.target.id,
            current_family_id=self.family.id,
        )

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()
        engine.dispose()

    def test_registers_query_tools_without_changing_daily_brief_set(self) -> None:
        self.assertEqual({tool.metadata.name for tool in self.registry.list_tools()}, QUERY_TOOL_NAMES)

    def test_metric_summary_tool_uses_service_and_safe_output(self) -> None:
        health_data_service.add_metric(
            self.db,
            user_id=self.actor.id,
            metric_type="sleep_duration",
            value_numeric=7.5,
            unit="hours",
        )

        result = self.executor.execute(
            self.db,
            self._request(
                "health_data.metric.summary",
                {"metric_type": "sleep_duration", "days": 7, "aggregation": "avg"},
                target_user_id=self.actor.id,
            ),
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.output_data["summary"]["count"], 1)
        self.assertNotIn("raw_text", str(result.output_data))
        self.assertNotIn("file_path", str(result.output_data))

    def test_documents_query_does_not_return_file_path_or_raw_text(self) -> None:
        document_service.create_document_metadata(
            self.db,
            user_id=self.actor.id,
            uploaded_by_user_id=self.actor.id,
            document_type=DocumentType.LAB_TEST,
            title="演示检查资料",
            file_name="demo-report.pdf",
            file_path="storage://private/demo-report.pdf",
        )

        result = self.executor.execute(self.db, self._request("documents.query", {"limit": 10}, target_user_id=self.actor.id))
        payload_text = str(result.output_data).lower()

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.output_data["count"], 1)
        self.assertNotIn("file_path", payload_text)
        self.assertNotIn("storage://", payload_text)
        self.assertNotIn("raw_extracted_text", payload_text)

    def test_family_permission_denied_blocks_metric_query_without_target_data(self) -> None:
        health_data_service.add_metric(
            self.db,
            user_id=self.target.id,
            metric_type="steps",
            value_numeric=12345,
            unit="steps",
        )
        permissions_service.update_share_permission(
            self.db,
            actor_user_id=self.actor.id,
            family_id=self.family.id,
            target_user_id=self.target.id,
            updates={"share_all": False, "can_view_metrics": False},
        )

        result = self.executor.execute(
            self.db,
            self._request(
                "health_data.metric.summary",
                {"metric_type": "steps", "days": 7},
                target_user_id=self.target.id,
                family_id=self.family.id,
            ),
        )

        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.error_code, "permission_denied")
        self.assertIsNone(result.output_data)
        self.assertNotIn("12345", result.message)

    def test_symptom_query_omits_raw_health_text(self) -> None:
        health_record_service.create_symptom_record(
            self.db,
            user_id=self.actor.id,
            created_by_user_id=self.actor.id,
            raw_text="very private symptom text",
            symptom_name="headache",
        )

        result = self.executor.execute(
            self.db,
            self._request("health_record.symptoms.query", {"days": 7}, target_user_id=self.actor.id),
        )
        payload_text = str(result.output_data).lower()

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.output_data["summary"]["count"], 1)
        self.assertNotIn("very private symptom text", payload_text)
        self.assertNotIn("raw_text", payload_text)

    def _request(
        self,
        tool_name: str,
        input_data: dict | None = None,
        *,
        target_user_id=None,
        family_id=None,
    ) -> ToolExecutionRequest:
        return ToolExecutionRequest(
            trace_id=self.trace.id,
            tool_name=tool_name,
            actor_user_id=self.actor.id,
            target_user_id=target_user_id or self.actor.id,
            family_id=family_id,
            input_data=input_data or {},
            reason="unit-test",
        )


if __name__ == "__main__":
    unittest.main()
