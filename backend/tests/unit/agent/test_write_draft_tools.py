from __future__ import annotations

import inspect
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_phase07g_write_draft_tools.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")

from app.agent import service as agent_service  # noqa: E402
from app.agent.enums import AgentToolCallStatus, AgentWorkflowName  # noqa: E402
from app.agent.schemas import ToolExecutionRequest  # noqa: E402
from app.agent.tool_executor import AgentToolExecutor  # noqa: E402
from app.agent.tool_registry import AgentToolRegistry  # noqa: E402
from app.agent.tools import register_write_draft_tools  # noqa: E402
from app.agent.tools import alert_tools, document_tools, health_record_tools  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.modules.alerts.models import Alert  # noqa: E402
from app.modules.document_center import service as document_service  # noqa: E402
from app.modules.document_center.enums import DocumentType  # noqa: E402
from app.modules.document_processing import service as document_processing_service  # noqa: E402
from app.modules.document_processing.models import MedicalEventDraft  # noqa: E402
from app.modules.family import service as family_service  # noqa: E402
from app.modules.health_record.models import HealthRecordDraft, SymptomRecord  # noqa: E402
from app.modules.identity import service as identity_service  # noqa: E402
from app.modules.medical_timeline.models import MedicalEvent  # noqa: E402
from app.modules.permissions import service as permissions_service  # noqa: E402
from app.modules.reports.models import DailyReport  # noqa: E402


WRITE_TOOL_NAMES = {
    "health_record.symptom_draft.create": ("health_record", "draft", "medium", "symptoms", "create"),
    "document_processing.medical_event_draft.create": ("document", "draft", "high", "medical_events", "create"),
    "alerts.create": ("alert", "write", "medium", "alerts", "create"),
}


class WriteDraftToolsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        engine.dispose()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        suffix = uuid4().hex[:8]
        self.actor = identity_service.create_user(
            self.db,
            email=f"phase07g.actor.{suffix}@example.com",
            phone=f"p07g_actor_{suffix}",
            nickname="Actor",
        )
        self.target = identity_service.create_user(
            self.db,
            email=f"phase07g.target.{suffix}@example.com",
            phone=f"p07g_target_{suffix}",
            nickname="Target",
        )
        self.other = identity_service.create_user(
            self.db,
            email=f"phase07g.other.{suffix}@example.com",
            phone=f"p07g_other_{suffix}",
            nickname="Other",
        )
        self.family = family_service.create_family_with_owner(
            self.db,
            owner_user_id=self.actor.id,
            family_name="Phase 07G Family",
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
        self.registry = register_write_draft_tools(AgentToolRegistry())
        self.executor = AgentToolExecutor(self.registry)
        self.trace = agent_service.start_trace(
            self.db,
            request_id=f"write-draft-tools-{uuid4()}",
            workflow_name=AgentWorkflowName.CHAT_WORKFLOW,
            current_user_id=self.actor.id,
            target_user_id=self.target.id,
            current_family_id=self.family.id,
        )

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()
        engine.dispose()

    def test_registers_all_write_draft_tools(self) -> None:
        self.assertEqual({tool.metadata.name for tool in self.registry.list_tools()}, set(WRITE_TOOL_NAMES))

    def test_write_tool_metadata_is_correct(self) -> None:
        for tool_name, expected in WRITE_TOOL_NAMES.items():
            category, access_mode, risk_level, permission_type, action = expected
            metadata = self.registry.get_tool(tool_name).metadata
            self.assertEqual(metadata.category, category)
            self.assertEqual(metadata.access_mode, access_mode)
            self.assertEqual(metadata.risk_level, risk_level)
            self.assertEqual(metadata.required_permission_type, permission_type)
            self.assertEqual(metadata.required_permission_action, action)
            self.assertTrue(metadata.requires_confirmation)

    def test_unconfirmed_symptom_draft_is_blocked_without_write(self) -> None:
        before = self._business_counts()

        result = self.executor.execute(
            self.db,
            self._request("health_record.symptom_draft.create", {"raw_text": "  最近头疼，想先记录一下  "}, confirmed=False),
        )
        call = agent_service.list_tool_calls(self.db, trace_id=self.trace.id)[0]

        self.assertEqual(result.status, "blocked")
        self.assertTrue(result.requires_confirmation)
        self.assertEqual(result.error_code, "confirmation_required")
        self.assertEqual(call.status, AgentToolCallStatus.BLOCKED_BY_GUARD)
        self.assertEqual(self._business_counts(), before)

    def test_confirmed_symptom_draft_creates_pending_draft_only(self) -> None:
        result = self.executor.execute(
            self.db,
            self._request("health_record.symptom_draft.create", {"raw_text": "  最近头疼，想先记录一下  "}, confirmed=True),
        )

        self.assertEqual(result.status, "completed")
        self.assertIn("draft_id", result.output_data)
        self.assertEqual(result.output_data["status"], "pending")
        self.assertEqual(self.db.query(HealthRecordDraft).count(), 1)
        self.assertEqual(self.db.query(SymptomRecord).count(), 0)
        self.assertNotIn("最近头疼", str(result.output_data))

    def test_unconfirmed_medical_event_draft_is_blocked_without_write(self) -> None:
        before = self._business_counts()

        result = self.executor.execute(
            self.db,
            self._request(
                "document_processing.medical_event_draft.create",
                {"draft_title": "复查记录", "summary": "用户提供的复查信息"},
                confirmed=False,
            ),
        )

        self.assertEqual(result.error_code, "confirmation_required")
        self.assertEqual(self._business_counts(), before)

    def test_confirmed_medical_event_draft_creates_pending_draft_only(self) -> None:
        result = self.executor.execute(
            self.db,
            self._request(
                "document_processing.medical_event_draft.create",
                {"draft_title": "复查记录", "summary": "用户提供的复查信息", "draft_event_type": "follow_up"},
                confirmed=True,
            ),
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.output_data["status"], "pending")
        self.assertEqual(self.db.query(MedicalEventDraft).count(), 1)
        self.assertEqual(self.db.query(MedicalEvent).count(), 0)
        self.assertNotIn("用户提供的复查信息", str(result.output_data))

    def test_medical_event_draft_rejects_cross_user_source_document(self) -> None:
        document = document_service.create_document_metadata(
            self.db,
            user_id=self.other.id,
            uploaded_by_user_id=self.other.id,
            document_type=DocumentType.CHECKUP_REPORT,
            title="Other document",
            file_name="other.pdf",
            file_path="demo://other.pdf",
        )

        result = self.executor.execute(
            self.db,
            self._request(
                "document_processing.medical_event_draft.create",
                {"draft_title": "复查记录", "source_document_id": str(document.id)},
                confirmed=True,
            ),
        )

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_code, "tool_execution_failed")
        self.assertEqual(self.db.query(MedicalEventDraft).count(), 0)
        self.assertNotIn("Other document", result.message)

    def test_medical_event_draft_rejects_cross_family_extraction_result(self) -> None:
        document = document_service.create_document_metadata(
            self.db,
            user_id=self.target.id,
            uploaded_by_user_id=self.actor.id,
            family_id=None,
            document_type=DocumentType.CHECKUP_REPORT,
            title="Personal document",
            file_name="personal.pdf",
            file_path="demo://personal.pdf",
        )
        extraction = document_processing_service.save_extraction_result(
            self.db,
            document_id=document.id,
            user_id=self.target.id,
            family_id=None,
            ai_summary="private extraction summary",
            raw_extracted_text="raw text should never appear",
        )

        result = self.executor.execute(
            self.db,
            self._request(
                "document_processing.medical_event_draft.create",
                {"draft_title": "复查记录", "extraction_result_id": str(extraction.id)},
                confirmed=True,
                family_id=self.family.id,
            ),
        )

        self.assertEqual(result.status, "failed")
        self.assertEqual(self.db.query(MedicalEventDraft).count(), 0)
        self.assertNotIn("private extraction summary", result.message)
        self.assertNotIn("raw text should never appear", str(result.output_data))

    def test_unconfirmed_alert_create_is_blocked_without_write(self) -> None:
        before = self._business_counts()

        result = self.executor.execute(
            self.db,
            self._request("alerts.create", self._alert_payload(), confirmed=False),
        )

        self.assertEqual(result.error_code, "confirmation_required")
        self.assertEqual(self._business_counts(), before)

    def test_confirmed_alert_create_creates_alert_without_medical_advice(self) -> None:
        result = self.executor.execute(
            self.db,
            self._request("alerts.create", self._alert_payload(), confirmed=True),
        )

        self.assertEqual(result.status, "completed")
        self.assertIn("alert_id", result.output_data)
        self.assertEqual(result.output_data["status"], "active")
        self.assertEqual(self.db.query(Alert).count(), 1)
        output_text = str(result.output_data).lower()
        self.assertNotIn("diagnosis", output_text)
        self.assertNotIn("prescription", output_text)
        self.assertNotIn("dosage", output_text)
        self.assertNotIn("stop medication", output_text)
        self.assertNotIn("file_path", output_text)
        self.assertNotIn("raw_extracted_text", output_text)
        self.assertNotIn("token", output_text)
        self.assertNotIn("password", output_text)
        self.assertNotIn("api_key", output_text)

    def test_alert_create_rejects_unsafe_medical_advice(self) -> None:
        result = self.executor.execute(
            self.db,
            self._request(
                "alerts.create",
                {
                    "title": "用药提醒",
                    "message": "停药并调整剂量",
                    "alert_type": "medication_reminder",
                    "level": "info",
                },
                confirmed=True,
            ),
        )

        self.assertEqual(result.status, "failed")
        self.assertEqual(self.db.query(Alert).count(), 0)
        self.assertNotIn("停药", result.message)
        self.assertNotIn("剂量", result.message)

    def test_family_permission_allowed_can_create_draft_and_alert(self) -> None:
        symptom_result = self.executor.execute(
            self.db,
            self._request("health_record.symptom_draft.create", {"raw_text": "家人代记一条症状"}, confirmed=True),
        )
        alert_result = self.executor.execute(
            self.db,
            self._request("alerts.create", self._alert_payload(), confirmed=True),
        )

        self.assertEqual(symptom_result.status, "completed")
        self.assertEqual(alert_result.status, "completed")
        self.assertEqual(self.db.query(HealthRecordDraft).count(), 1)
        self.assertEqual(self.db.query(Alert).count(), 1)

    def test_alert_create_requires_dedicated_create_permission_not_view(self) -> None:
        permissions_service.update_share_permission(
            self.db,
            actor_user_id=self.actor.id,
            family_id=self.family.id,
            target_user_id=self.target.id,
            updates={
                "share_all": False,
                "can_view_alerts": True,
                "can_create_alerts": False,
            },
        )

        result = self.executor.execute(
            self.db,
            self._request("alerts.create", self._alert_payload(), confirmed=True),
        )
        call = agent_service.list_tool_calls(self.db, trace_id=self.trace.id)[0]

        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.error_code, "permission_denied")
        self.assertEqual(call.status, AgentToolCallStatus.BLOCKED_BY_PERMISSION)
        self.assertEqual(call.permission_result["permission_type"], "alerts")
        self.assertEqual(call.permission_result["action"], "create")
        self.assertEqual(self.db.query(Alert).count(), 0)

    def test_family_permission_denied_blocks_without_target_data(self) -> None:
        permissions_service.update_share_permission(
            self.db,
            actor_user_id=self.actor.id,
            family_id=self.family.id,
            target_user_id=self.target.id,
            updates={"can_create_symptom_records": False},
        )

        result = self.executor.execute(
            self.db,
            self._request("health_record.symptom_draft.create", {"raw_text": "secret target symptom"}, confirmed=True),
        )
        call = agent_service.list_tool_calls(self.db, trace_id=self.trace.id)[0]

        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.error_code, "permission_denied")
        self.assertEqual(call.status, AgentToolCallStatus.BLOCKED_BY_PERMISSION)
        self.assertEqual(self.db.query(HealthRecordDraft).count(), 0)
        self.assertNotIn("secret target symptom", result.message)

    def test_tool_calls_completed_and_blocked_are_recorded(self) -> None:
        self.executor.execute(self.db, self._request("health_record.symptom_draft.create", {"raw_text": "记录症状"}, confirmed=True))
        permissions_service.update_share_permission(
            self.db,
            actor_user_id=self.actor.id,
            family_id=self.family.id,
            target_user_id=self.target.id,
            updates={"share_all": False, "can_create_alerts": False},
        )
        self.executor.execute(self.db, self._request("alerts.create", self._alert_payload(), confirmed=True))
        calls = agent_service.list_tool_calls(self.db, trace_id=self.trace.id)

        self.assertEqual(calls[0].status, AgentToolCallStatus.SUCCESS)
        self.assertEqual(calls[1].status, AgentToolCallStatus.BLOCKED_BY_PERMISSION)
        self.assertTrue(calls[1].permission_checked)
        self.assertFalse(calls[1].permission_result["allowed"])

    def test_outputs_and_tool_call_summaries_do_not_include_sensitive_fields(self) -> None:
        result = self.executor.execute(
            self.db,
            self._request(
                "health_record.symptom_draft.create",
                {
                    "raw_text": "记录症状，不需要回显全文",
                    "token": "secret-token",
                    "file_path": "C:/Users/person/secret.pdf",
                    "raw_extracted_text": "full extraction",
                },
                confirmed=True,
            ),
        )
        call = agent_service.list_tool_calls(self.db, trace_id=self.trace.id)[0]
        combined = f"{result.output_data} {call.input_summary} {call.output_summary}".lower()

        self.assertNotIn("raw_text", combined)
        self.assertNotIn("记录症状，不需要回显全文", combined)
        self.assertNotIn("file_path", combined)
        self.assertNotIn("raw_extracted_text", combined)
        self.assertNotIn("secret-token", combined)
        self.assertNotIn("password", combined)
        self.assertNotIn("api_key", combined)

    def test_tools_do_not_call_llm_or_import_repositories(self) -> None:
        sys.modules.pop("app.agent.llm_client", None)
        self.executor.execute(self.db, self._request("alerts.create", self._alert_payload(), confirmed=True))

        self.assertNotIn("app.agent.llm_client", sys.modules)
        for module in [alert_tools, document_tools, health_record_tools]:
            source = inspect.getsource(module)
            self.assertNotIn("repository", source)
            self.assertNotIn("SessionLocal", source)
            self.assertNotIn("select(", source)

    def test_write_tools_do_not_write_daily_reports(self) -> None:
        before = self.db.query(DailyReport).count()

        self.executor.execute(self.db, self._request("health_record.symptom_draft.create", {"raw_text": "记录症状"}, confirmed=True))
        self.executor.execute(
            self.db,
            self._request(
                "document_processing.medical_event_draft.create",
                {"draft_title": "复查记录", "summary": "用户提供的复查信息"},
                confirmed=True,
            ),
        )
        self.executor.execute(self.db, self._request("alerts.create", self._alert_payload(), confirmed=True))

        self.assertEqual(self.db.query(DailyReport).count(), before)

    def _request(
        self,
        tool_name: str,
        input_data: dict | None = None,
        *,
        confirmed: bool,
        family_id=None,
    ) -> ToolExecutionRequest:
        return ToolExecutionRequest(
            trace_id=self.trace.id,
            tool_name=tool_name,
            actor_user_id=self.actor.id,
            target_user_id=self.target.id,
            family_id=self.family.id if family_id is None else family_id,
            input_data=input_data or {},
            confirmed=confirmed,
            reason="unit-test",
        )

    def _alert_payload(self) -> dict:
        return {
            "alert_type": "medical_follow_up",
            "level": "info",
            "title": "复查提醒",
            "message": "请按自己的计划记录复查安排。",
            "suggested_action": "准备就医沟通材料。",
            "due_at": datetime.now(timezone.utc).isoformat(),
        }

    def _business_counts(self) -> dict[str, int]:
        return {
            "health_record_drafts": self.db.query(HealthRecordDraft).count(),
            "symptom_records": self.db.query(SymptomRecord).count(),
            "medical_event_drafts": self.db.query(MedicalEventDraft).count(),
            "medical_events": self.db.query(MedicalEvent).count(),
            "alerts": self.db.query(Alert).count(),
            "daily_reports": self.db.query(DailyReport).count(),
        }


if __name__ == "__main__":
    unittest.main()
