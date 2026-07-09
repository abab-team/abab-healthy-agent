from __future__ import annotations

import inspect
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_phase24_workflows.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")

from app.agent import service as agent_service  # noqa: E402
from app.agent.enums import AgentTraceStatus, AgentWorkflowName  # noqa: E402
from app.agent.runtime import AgentRuntime  # noqa: E402
from app.agent.schemas import AgentRunRequest  # noqa: E402
from app.agent.workflows import default_workflow_registry  # noqa: E402
from app.agent.workflows.doctor_visit_summary_workflow import DoctorVisitSummaryWorkflow  # noqa: E402
from app.agent.workflows.free_text_record_workflow import FreeTextRecordWorkflow  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.modules.alerts import service as alert_service  # noqa: E402
from app.modules.alerts.enums import AlertLevel, AlertType  # noqa: E402
from app.modules.document_center import service as document_service  # noqa: E402
from app.modules.document_center.enums import DocumentType  # noqa: E402
from app.modules.document_processing.models import MedicalEventDraft  # noqa: E402
from app.modules.family import service as family_service  # noqa: E402
from app.modules.health_data import service as health_data_service  # noqa: E402
from app.modules.health_data.models import BloodPressureRecord  # noqa: E402
from app.modules.health_record import service as health_record_service  # noqa: E402
from app.modules.health_record.models import HealthRecordDraft, SymptomRecord  # noqa: E402
from app.modules.identity import service as identity_service  # noqa: E402
from app.modules.medical_timeline import service as medical_timeline_service  # noqa: E402
from app.modules.medical_timeline.enums import MedicalEventType  # noqa: E402
from app.modules.medical_timeline.models import MedicalEvent  # noqa: E402
from app.modules.permissions import service as permissions_service  # noqa: E402
from app.modules.reports.models import DailyReport  # noqa: E402


FORBIDDEN_OUTPUT_TERMS = (
    "diagnosis",
    "prescription",
    "dosage",
    "stop medication",
    "normal",
    "abnormal",
    "high risk",
    "low risk",
    "file_path",
    "raw_extracted_text",
    "private raw symptom",
)


class Phase24WorkflowTestCase(unittest.TestCase):
    def setUp(self) -> None:
        engine.dispose()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        suffix = uuid4().hex[:8]
        self.actor = identity_service.create_user(
            self.db,
            email=f"phase24.actor.{suffix}@example.com",
            phone=f"p24_actor_{suffix}",
            nickname="Actor",
        )
        self.target = identity_service.create_user(
            self.db,
            email=f"phase24.target.{suffix}@example.com",
            phone=f"p24_target_{suffix}",
            nickname="Target",
        )
        self.family = family_service.create_family_with_owner(
            self.db,
            owner_user_id=self.actor.id,
            family_name="Phase 24 Family",
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

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()
        engine.dispose()

    def test_phase24_workflows_are_registered(self) -> None:
        registry = default_workflow_registry()

        self.assertIsInstance(registry.get(AgentWorkflowName.FREE_TEXT_RECORD_WORKFLOW), FreeTextRecordWorkflow)
        self.assertIsInstance(registry.get(AgentWorkflowName.DOCTOR_VISIT_SUMMARY_WORKFLOW), DoctorVisitSummaryWorkflow)

    def test_free_text_record_preview_does_not_write_draft_or_formal_record(self) -> None:
        before = self._business_counts()

        result = AgentRuntime().run(
            self.db,
            self._request(
                "free_text_record_workflow",
                self.actor.id,
                self.actor.id,
                user_message="I want to record a mild headache after a long screen day.",
                confirmation=False,
            ),
        )

        self.assertEqual(result.status, "completed")
        self.assertIn("preview for a pending health note draft", result.generated_content or "")
        self.assertEqual(result.tool_calls_count, 1)
        self.assertEqual(self._business_counts(), before)

    def test_free_text_record_confirm_creates_pending_draft_only(self) -> None:
        result = AgentRuntime().run(
            self.db,
            self._request(
                "free_text_record_workflow",
                self.actor.id,
                self.actor.id,
                user_message="I want to record a mild headache after a long screen day.",
                confirmation=True,
            ),
        )

        self.assertEqual(result.status, "completed")
        self.assertIn("pending health note draft", result.generated_content or "")
        self.assertIn("formal_health_fact_created=false", result.generated_content or "")
        self.assertEqual(self.db.query(HealthRecordDraft).count(), 1)
        self.assertEqual(self.db.query(SymptomRecord).count(), 0)
        self.assertEqual(self.db.query(MedicalEvent).count(), 0)
        self.assertEqual(self.db.query(DailyReport).count(), 0)

    def test_free_text_record_emergency_input_is_blocked_before_tool_execution(self) -> None:
        result = AgentRuntime().run(
            self.db,
            self._request(
                "free_text_record_workflow",
                self.actor.id,
                self.actor.id,
                user_message="I have chest pain and difficulty breathing.",
                confirmation=True,
            ),
        )
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)
        trace = agent_service.get_trace(self.db, result.trace_id)

        self.assertEqual(result.status, "blocked")
        self.assertEqual(trace.status, AgentTraceStatus.BLOCKED)
        self.assertEqual(calls, [])
        self.assertEqual(self.db.query(HealthRecordDraft).count(), 0)

    def test_doctor_visit_summary_generates_readonly_safe_package(self) -> None:
        self._seed_records()
        before = self._business_counts()

        result = AgentRuntime().run(
            self.db,
            self._request(
                "doctor_visit_summary_workflow",
                self.actor.id,
                self.target.id,
                family_id=self.family.id,
                user_message="Prepare records for a clinician visit based on system records.",
            ),
        )
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)
        content = (result.generated_content or "").lower()

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tool_calls_count, 5)
        self.assertEqual(len(calls), 5)
        self.assertTrue(all(call.status.value == "success" for call in calls))
        self.assertEqual(self._business_counts(), before)
        self.assertIn("based on system records only", content)
        self.assertIn("does not replace a doctor's judgment", content)
        for term in FORBIDDEN_OUTPUT_TERMS:
            self.assertNotIn(term, content)

    def test_doctor_visit_summary_permission_denied_does_not_leak_target_data(self) -> None:
        self._seed_records(secret_text="private raw symptom hidden from actor")
        permissions_service.update_share_permission(
            self.db,
            actor_user_id=self.actor.id,
            family_id=self.family.id,
            target_user_id=self.target.id,
            updates={
                "share_all": False,
                "can_view_metrics": False,
                "can_view_symptoms": False,
                "can_view_medical_events": False,
                "can_view_documents": False,
                "can_view_alerts": False,
            },
        )

        result = AgentRuntime().run(
            self.db,
            self._request(
                "doctor_visit_summary_workflow",
                self.actor.id,
                self.target.id,
                family_id=self.family.id,
                user_message="Prepare records for a clinician visit based on system records.",
            ),
        )
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)
        content = result.generated_content or ""

        self.assertEqual(result.status, "completed")
        self.assertEqual(len(calls), 5)
        self.assertTrue(all(call.status.value == "blocked_by_permission" for call in calls))
        self.assertIn("Some information is unavailable", content)
        self.assertNotIn("private raw symptom hidden from actor", content)

    def test_phase24_workflows_do_not_import_repositories_or_llm(self) -> None:
        sys.modules.pop("app.llm.client", None)
        modules = [
            sys.modules[FreeTextRecordWorkflow.__module__],
            sys.modules[DoctorVisitSummaryWorkflow.__module__],
        ]

        for module in modules:
            source = inspect.getsource(module)
            self.assertNotIn("repository", source)
            self.assertNotIn("SessionLocal", source)
            self.assertNotIn("select(", source)
            self.assertNotIn(".query(", source)
            self.assertNotIn("get_llm_client", source)

    def _request(
        self,
        workflow_type: str,
        actor_user_id,
        target_user_id,
        *,
        family_id=None,
        user_message: str,
        confirmation: bool = False,
        workflow_payload: dict | None = None,
    ) -> AgentRunRequest:
        return AgentRunRequest(
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            family_id=family_id,
            workflow_type=workflow_type,
            user_message=user_message,
            source="unit-test",
            confirmation=confirmation,
            workflow_payload=workflow_payload,
        )

    def _seed_records(self, *, secret_text: str = "private raw symptom") -> None:
        health_data_service.add_blood_pressure_record(
            self.db,
            user_id=self.target.id,
            systolic=118,
            diastolic=76,
            pulse=70,
        )
        health_record_service.create_symptom_record(
            self.db,
            user_id=self.target.id,
            family_id=self.family.id,
            created_by_user_id=self.actor.id,
            raw_text=secret_text,
            symptom_name="headache",
        )
        medical_timeline_service.create_medical_event(
            self.db,
            user_id=self.target.id,
            family_id=self.family.id,
            created_by_user_id=self.actor.id,
            event_type=MedicalEventType.FOLLOW_UP,
            title="Follow-up note",
            follow_up_needed=True,
            follow_up_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        document_service.create_document_metadata(
            self.db,
            user_id=self.target.id,
            family_id=self.family.id,
            uploaded_by_user_id=self.actor.id,
            document_type=DocumentType.CHECKUP_REPORT,
            title="Checkup document",
            file_name="checkup.pdf",
            file_path="demo://checkup.pdf",
        )
        alert_service.create_alert(
            self.db,
            user_id=self.target.id,
            family_id=self.family.id,
            created_by_user_id=self.actor.id,
            alert_type=AlertType.MEDICAL_FOLLOW_UP,
            level=AlertLevel.INFO,
            title="Visit reminder",
            message="Bring system records to the clinician visit.",
        )

    def _business_counts(self) -> dict[str, int]:
        return {
            "blood_pressure_records": self.db.query(BloodPressureRecord).count(),
            "symptom_records": self.db.query(SymptomRecord).count(),
            "health_record_drafts": self.db.query(HealthRecordDraft).count(),
            "medical_events": self.db.query(MedicalEvent).count(),
            "medical_event_drafts": self.db.query(MedicalEventDraft).count(),
            "daily_reports": self.db.query(DailyReport).count(),
        }


if __name__ == "__main__":
    unittest.main()
