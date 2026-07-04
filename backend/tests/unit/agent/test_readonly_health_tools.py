from __future__ import annotations

import inspect
import os
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_phase07e_readonly_tools.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")

from app.agent import service as agent_service  # noqa: E402
from app.agent.enums import AgentToolCallStatus, AgentWorkflowName  # noqa: E402
from app.agent.schemas import ToolExecutionRequest  # noqa: E402
from app.agent.tool_executor import AgentToolExecutor  # noqa: E402
from app.agent.tool_registry import AgentToolRegistry  # noqa: E402
from app.agent.tools import register_readonly_health_tools  # noqa: E402
from app.agent.tools import alert_tools, health_data_tools, health_profile_tools, health_record_tools, medical_timeline_tools  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.modules.alerts import service as alert_service  # noqa: E402
from app.modules.alerts.enums import AlertLevel, AlertType  # noqa: E402
from app.modules.alerts.models import Alert  # noqa: E402
from app.modules.family import service as family_service  # noqa: E402
from app.modules.health_data import service as health_data_service  # noqa: E402
from app.modules.health_data.models import BloodPressureRecord  # noqa: E402
from app.modules.health_profile import service as health_profile_service  # noqa: E402
from app.modules.health_profile.models import HealthProfile  # noqa: E402
from app.modules.health_record import service as health_record_service  # noqa: E402
from app.modules.health_record.models import SymptomRecord  # noqa: E402
from app.modules.identity import service as identity_service  # noqa: E402
from app.modules.identity.enums import Gender  # noqa: E402
from app.modules.medical_timeline import service as medical_timeline_service  # noqa: E402
from app.modules.medical_timeline.enums import MedicalEventType  # noqa: E402
from app.modules.medical_timeline.models import MedicalEvent  # noqa: E402
from app.modules.permissions import service as permissions_service  # noqa: E402


TOOL_NAMES = {
    "health_profile.get": ("health_profile", "health_profile"),
    "health_data.blood_pressure.summary": ("health_data", "metrics"),
    "health_record.symptoms.summary": ("health_record", "symptoms"),
    "medical_timeline.followups.list": ("medical_timeline", "medical_events"),
    "alerts.active.list": ("alert", "alerts"),
}


class ReadonlyHealthToolsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        engine.dispose()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        suffix = uuid4().hex[:8]
        self.actor = identity_service.create_user(
            self.db,
            email=f"phase07e.actor.{suffix}@example.com",
            phone=f"p07e_actor_{suffix}",
            nickname="Actor",
        )
        self.target = identity_service.create_user(
            self.db,
            email=f"phase07e.target.{suffix}@example.com",
            phone=f"p07e_target_{suffix}",
            nickname="Target",
            gender=Gender.FEMALE,
            birth_date=date(1988, 1, 1),
        )
        self.family = family_service.create_family_with_owner(
            self.db,
            owner_user_id=self.actor.id,
            family_name="Phase 07E Family",
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
        self.registry = register_readonly_health_tools(AgentToolRegistry())
        self.executor = AgentToolExecutor(self.registry)
        self.trace = agent_service.start_trace(
            self.db,
            request_id=f"readonly-tools-{uuid4()}",
            workflow_name=AgentWorkflowName.CHAT_WORKFLOW,
            current_user_id=self.actor.id,
            target_user_id=self.target.id,
            current_family_id=self.family.id,
        )

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()
        engine.dispose()

    def test_registers_all_readonly_health_tools(self) -> None:
        self.assertEqual({tool.metadata.name for tool in self.registry.list_tools()}, set(TOOL_NAMES))

    def test_tool_metadata_permission_declarations_are_correct(self) -> None:
        for tool_name, (category, permission_type) in TOOL_NAMES.items():
            metadata = self.registry.get_tool(tool_name).metadata
            self.assertEqual(metadata.category, category)
            self.assertEqual(metadata.access_mode, "read")
            self.assertIn(metadata.risk_level, {"low", "medium"})
            self.assertFalse(metadata.requires_confirmation)
            self.assertEqual(metadata.required_permission_type, permission_type)
            self.assertEqual(metadata.required_permission_action, "view")

    def test_self_access_health_profile_get_success(self) -> None:
        health_profile_service.create_or_update_profile(
            self.db,
            self.actor.id,
            {"health_goal": "walk weekly", "allergy_summary": "pollen"},
        )

        result = self.executor.execute(self.db, self._request("health_profile.get", target_user_id=self.actor.id))

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.output_data["profile"]["health_goal"], "walk weekly")
        self.assertNotIn("password", str(result.output_data).lower())

    def test_self_access_blood_pressure_summary_success(self) -> None:
        health_data_service.add_blood_pressure_record(
            self.db,
            user_id=self.actor.id,
            systolic=118,
            diastolic=76,
            pulse=70,
        )

        result = self.executor.execute(self.db, self._request("health_data.blood_pressure.summary", target_user_id=self.actor.id))

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.output_data["summary"]["count"], 1)
        self.assertNotIn("normal", str(result.output_data).lower())
        self.assertNotIn("abnormal", str(result.output_data).lower())
        self.assertNotIn("hypertension", str(result.output_data).lower())

    def test_self_access_symptoms_summary_success(self) -> None:
        health_record_service.create_symptom_record(
            self.db,
            user_id=self.actor.id,
            created_by_user_id=self.actor.id,
            raw_text="Headache after long screen time.",
            symptom_name="headache",
        )

        result = self.executor.execute(self.db, self._request("health_record.symptoms.summary", target_user_id=self.actor.id))

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.output_data["summary"]["count"], 1)
        self.assertNotIn("raw_text", str(result.output_data))
        self.assertNotIn("cause", str(result.output_data).lower())

    def test_self_access_followups_list_success(self) -> None:
        medical_timeline_service.create_medical_event(
            self.db,
            user_id=self.actor.id,
            created_by_user_id=self.actor.id,
            event_type=MedicalEventType.FOLLOW_UP,
            title="Follow-up record",
            follow_up_needed=True,
            follow_up_at=datetime.now(timezone.utc) + timedelta(days=3),
            doctor_advice="Long private doctor advice should not be returned.",
        )

        result = self.executor.execute(self.db, self._request("medical_timeline.followups.list", target_user_id=self.actor.id))

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.output_data["count"], 1)
        self.assertNotIn("doctor_advice", str(result.output_data))
        self.assertNotIn("treatment plan", str(result.output_data).lower())

    def test_self_access_active_alerts_list_success(self) -> None:
        alert_service.create_alert(
            self.db,
            user_id=self.actor.id,
            alert_type=AlertType.DOCUMENT_REVIEW,
            level=AlertLevel.ATTENTION,
            title="Review document",
            message="Document review reminder.",
        )

        result = self.executor.execute(self.db, self._request("alerts.active.list", target_user_id=self.actor.id))

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.output_data["count"], 1)
        self.assertNotIn("body is fine", str(result.output_data).lower())

    def test_family_access_allowed_executes_tool(self) -> None:
        health_profile_service.create_or_update_profile(self.db, self.target.id, {"health_goal": "sleep routine"})

        result = self.executor.execute(
            self.db,
            self._request("health_profile.get", target_user_id=self.target.id, family_id=self.family.id),
        )
        call = agent_service.list_tool_calls(self.db, trace_id=self.trace.id)[0]

        self.assertEqual(result.status, "completed")
        self.assertTrue(call.permission_checked)
        self.assertTrue(call.permission_result["allowed"])

    def test_family_access_denied_blocks_without_target_data(self) -> None:
        permissions_service.update_share_permission(
            self.db,
            actor_user_id=self.actor.id,
            family_id=self.family.id,
            target_user_id=self.target.id,
            updates={"share_all": False, "can_view_profile": False},
        )
        health_profile_service.create_or_update_profile(self.db, self.target.id, {"health_goal": "secret target data"})

        result = self.executor.execute(
            self.db,
            self._request("health_profile.get", target_user_id=self.target.id, family_id=self.family.id),
        )
        call = agent_service.list_tool_calls(self.db, trace_id=self.trace.id)[0]

        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.error_code, "permission_denied")
        self.assertIsNone(result.output_data)
        self.assertEqual(call.status, AgentToolCallStatus.BLOCKED_BY_PERMISSION)
        self.assertNotIn("secret target data", result.message)

    def test_tool_call_completed_and_blocked_are_recorded(self) -> None:
        self.executor.execute(self.db, self._request("alerts.active.list", target_user_id=self.actor.id))
        self.executor.execute(self.db, self._request("alerts.active.list", target_user_id=self.target.id))
        calls = agent_service.list_tool_calls(self.db, trace_id=self.trace.id)

        self.assertEqual(calls[0].status, AgentToolCallStatus.SUCCESS)
        self.assertEqual(calls[1].status, AgentToolCallStatus.BLOCKED_BY_PERMISSION)

    def test_outputs_do_not_include_sensitive_fields(self) -> None:
        health_data_service.add_blood_pressure_record(self.db, user_id=self.actor.id, systolic=120, diastolic=80)

        for tool_name in TOOL_NAMES:
            result = self.executor.execute(self.db, self._request(tool_name, target_user_id=self.actor.id))
            output_text = str(result.output_data).lower()
            self.assertNotIn("file_path", output_text)
            self.assertNotIn("raw_extracted_text", output_text)
            self.assertNotIn("token", output_text)
            self.assertNotIn("password", output_text)
            self.assertNotIn("api_key", output_text)
            self.assertNotIn("private_key", output_text)

    def test_empty_alerts_do_not_claim_body_is_fine(self) -> None:
        result = self.executor.execute(self.db, self._request("alerts.active.list", target_user_id=self.actor.id))
        output_text = str(result.output_data).lower()

        self.assertTrue(result.output_data["empty"])
        self.assertNotIn("body is fine", output_text)
        self.assertNotIn("no health problem", output_text)

    def test_tools_do_not_call_llm_or_import_repositories(self) -> None:
        sys.modules.pop("app.agent.llm_client", None)
        self.executor.execute(self.db, self._request("health_profile.get", target_user_id=self.actor.id))

        self.assertNotIn("app.agent.llm_client", sys.modules)
        for module in [alert_tools, health_data_tools, health_profile_tools, health_record_tools, medical_timeline_tools]:
            source = inspect.getsource(module)
            self.assertNotIn("repository", source)

    def test_readonly_tools_do_not_write_business_data(self) -> None:
        counts_before = self._business_counts()

        for tool_name in TOOL_NAMES:
            self.executor.execute(self.db, self._request(tool_name, target_user_id=self.actor.id))

        self.assertEqual(self._business_counts(), counts_before)

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
            target_user_id=target_user_id or self.target.id,
            family_id=family_id,
            input_data=input_data or {},
            reason="unit-test",
        )

    def _business_counts(self) -> dict[str, int]:
        return {
            "health_profiles": self.db.query(HealthProfile).count(),
            "blood_pressure_records": self.db.query(BloodPressureRecord).count(),
            "symptom_records": self.db.query(SymptomRecord).count(),
            "medical_events": self.db.query(MedicalEvent).count(),
            "alerts": self.db.query(Alert).count(),
        }


if __name__ == "__main__":
    unittest.main()
