from __future__ import annotations

import inspect
import os
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_phase07f_daily_health_brief.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")

from app.agent import service as agent_service  # noqa: E402
from app.agent.enums import AgentTraceStatus, AgentWorkflowName  # noqa: E402
from app.agent.runtime import AgentRuntime  # noqa: E402
from app.agent.schemas import AgentRunRequest  # noqa: E402
from app.agent.workflows import AgentWorkflowRegistry, default_workflow_registry  # noqa: E402
from app.agent.workflows.daily_health_brief import DailyHealthBriefWorkflow  # noqa: E402
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
from app.modules.health_record.models import HealthRecordDraft, SymptomRecord  # noqa: E402
from app.modules.document_processing.models import MedicalEventDraft  # noqa: E402
from app.modules.identity import service as identity_service  # noqa: E402
from app.modules.identity.enums import Gender  # noqa: E402
from app.modules.medical_timeline import service as medical_timeline_service  # noqa: E402
from app.modules.medical_timeline.enums import MedicalEventType  # noqa: E402
from app.modules.medical_timeline.models import MedicalEvent  # noqa: E402
from app.modules.permissions import service as permissions_service  # noqa: E402
from app.modules.reports.models import DailyReport  # noqa: E402


READONLY_TOOL_NAMES = [
    "health_profile.get",
    "health_data.blood_pressure.summary",
    "health_record.symptoms.summary",
    "medical_timeline.followups.list",
    "alerts.active.list",
]
UNSAFE_OUTPUT_TERMS = (
    "正常",
    "异常",
    "高血压",
    "低血压",
    "prescription",
    "dosage",
    "stop medication",
    "take 2 pills",
    "不用看医生",
    "没有问题",
    "你很健康",
)


class DailyHealthBriefWorkflowTestCase(unittest.TestCase):
    def setUp(self) -> None:
        engine.dispose()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        suffix = uuid4().hex[:8]
        self.actor = identity_service.create_user(
            self.db,
            email=f"phase07f.actor.{suffix}@example.com",
            phone=f"p07f_actor_{suffix}",
            nickname="Actor",
        )
        self.target = identity_service.create_user(
            self.db,
            email=f"phase07f.target.{suffix}@example.com",
            phone=f"p07f_target_{suffix}",
            nickname="Target",
            gender=Gender.FEMALE,
            birth_date=date(1988, 1, 1),
        )
        self.family = family_service.create_family_with_owner(
            self.db,
            owner_user_id=self.actor.id,
            family_name="Phase 07F Family",
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

    def test_daily_health_brief_workflow_is_registered(self) -> None:
        handler = default_workflow_registry().get(AgentWorkflowName.DAILY_HEALTH_BRIEF)

        self.assertIsInstance(handler, DailyHealthBriefWorkflow)

    def test_runtime_executes_daily_health_brief_for_self_access(self) -> None:
        self._seed_health_records(self.actor.id, self.actor.id, family_id=None)

        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id))
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertFalse(result.blocked)
        self.assertEqual(result.workflow_type, "daily_health_brief")
        self.assertEqual(result.tool_calls_count, 5)
        self.assertEqual([call.tool_name for call in calls], READONLY_TOOL_NAMES)
        self.assertTrue(all(call.status.value == "success" for call in calls))
        self.assertIn("根据系统内记录", result.generated_content or "")
        self.assertIn("健康简报", result.generated_content or "")

    def test_family_access_allowed_generates_brief(self) -> None:
        self._seed_health_records(self.target.id, self.actor.id, family_id=self.family.id)

        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.target.id, family_id=self.family.id))
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertEqual(len(calls), 5)
        self.assertTrue(all(call.permission_checked for call in calls))
        self.assertIn("系统内共有", result.generated_content or "")

    def test_family_access_denied_does_not_leak_target_data(self) -> None:
        self._seed_health_records(self.target.id, self.actor.id, family_id=self.family.id, secret_text="private target symptom")
        permissions_service.update_share_permission(
            self.db,
            actor_user_id=self.actor.id,
            family_id=self.family.id,
            target_user_id=self.target.id,
            updates={
                "share_all": False,
                "can_view_profile": False,
                "can_view_metrics": False,
                "can_view_symptoms": False,
                "can_view_medical_events": False,
                "can_view_alerts": False,
            },
        )

        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.target.id, family_id=self.family.id))
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)
        content = result.generated_content or ""

        self.assertEqual(result.status, "completed")
        self.assertEqual(len(calls), 5)
        self.assertTrue(all(call.status.value == "blocked_by_permission" for call in calls))
        self.assertIn("部分信息因权限设置暂不可用", content)
        self.assertNotIn("private target symptom", content)

    def test_one_blocked_tool_still_returns_partial_safe_brief(self) -> None:
        self._seed_health_records(self.target.id, self.actor.id, family_id=self.family.id)
        permissions_service.update_share_permission(
            self.db,
            actor_user_id=self.actor.id,
            family_id=self.family.id,
            target_user_id=self.target.id,
            updates={
                "share_all": False,
                "can_view_profile": True,
                "can_view_metrics": True,
                "can_view_symptoms": False,
                "can_view_medical_events": True,
                "can_view_alerts": True,
            },
        )

        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.target.id, family_id=self.family.id))
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertEqual(len(calls), 5)
        self.assertIn("部分信息因权限设置暂不可用", result.generated_content or "")
        self.assertIn("根据系统内记录", result.generated_content or "")

    def test_no_records_uses_system_no_record_wording(self) -> None:
        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id))
        content = result.generated_content or ""

        self.assertIn("系统内暂无相关记录", content)
        self.assertNotIn("现实没有问题", content)
        self.assertNotIn("没有问题", content)

    def test_output_is_safe_and_output_safety_does_not_block(self) -> None:
        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id))
        content = result.generated_content or ""

        self.assertEqual(result.status, "completed")
        self.assertFalse(result.blocked)
        self.assertIn("不能替代医生诊断", content)
        self.assertIn("请联系医生或当地急救服务", content)
        for term in UNSAFE_OUTPUT_TERMS:
            self.assertNotIn(term, content)

    def test_workflow_does_not_call_llm_or_directly_access_repository_or_db(self) -> None:
        sys.modules.pop("app.agent.llm_client", None)
        source = inspect.getsource(sys.modules[DailyHealthBriefWorkflow.__module__])

        AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id))

        self.assertNotIn("app.agent.llm_client", sys.modules)
        self.assertNotIn("repository", source)
        self.assertNotIn("SessionLocal", source)
        self.assertNotIn("select(", source)
        self.assertNotIn(".query(", source)
        self.assertNotIn("service as", source)

    def test_workflow_does_not_write_daily_reports_or_health_business_data(self) -> None:
        self._seed_health_records(self.actor.id, self.actor.id, family_id=None)
        counts_before = self._business_counts()

        AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id))

        self.assertEqual(self._business_counts(), counts_before)

    def test_blocked_input_does_not_execute_workflow_or_tools(self) -> None:
        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id, user_message="   "))
        trace = agent_service.get_trace(self.db, result.trace_id)
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "blocked")
        self.assertEqual(trace.status, AgentTraceStatus.BLOCKED)
        self.assertEqual(calls, [])

    def test_trace_does_not_remain_running(self) -> None:
        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id))
        trace = agent_service.get_trace(self.db, result.trace_id)

        self.assertNotEqual(trace.status, AgentTraceStatus.RUNNING)

    def _request(self, actor_user_id, target_user_id, *, family_id=None, user_message: str = "整理最近健康记录") -> AgentRunRequest:
        return AgentRunRequest(
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            family_id=family_id,
            workflow_type="daily_health_brief",
            user_message=user_message,
            source="unit-test",
        )

    def _seed_health_records(self, user_id, created_by_user_id, *, family_id, secret_text: str = "headache after screen time") -> None:
        health_profile_service.create_or_update_profile(
            self.db,
            user_id,
            {"health_goal": "walk weekly", "allergy_summary": "pollen"},
        )
        health_data_service.add_blood_pressure_record(
            self.db,
            user_id=user_id,
            systolic=118,
            diastolic=76,
            pulse=70,
        )
        health_record_service.create_symptom_record(
            self.db,
            user_id=user_id,
            family_id=family_id,
            created_by_user_id=created_by_user_id,
            raw_text=secret_text,
            symptom_name="headache",
        )
        medical_timeline_service.create_medical_event(
            self.db,
            user_id=user_id,
            family_id=family_id,
            created_by_user_id=created_by_user_id,
            event_type=MedicalEventType.FOLLOW_UP,
            title="Follow-up record",
            follow_up_needed=True,
            follow_up_at=datetime.now(timezone.utc) + timedelta(days=3),
            doctor_advice="private doctor advice should not be returned",
        )
        alert_service.create_alert(
            self.db,
            user_id=user_id,
            family_id=family_id,
            created_by_user_id=created_by_user_id,
            alert_type=AlertType.DOCUMENT_REVIEW,
            level=AlertLevel.ATTENTION,
            title="Review document",
            message="Document review reminder.",
        )

    def _business_counts(self) -> dict[str, int]:
        return {
            "health_profiles": self.db.query(HealthProfile).count(),
            "blood_pressure_records": self.db.query(BloodPressureRecord).count(),
            "symptom_records": self.db.query(SymptomRecord).count(),
            "health_record_drafts": self.db.query(HealthRecordDraft).count(),
            "medical_events": self.db.query(MedicalEvent).count(),
            "medical_event_drafts": self.db.query(MedicalEventDraft).count(),
            "daily_reports": self.db.query(DailyReport).count(),
            "alerts": self.db.query(Alert).count(),
        }


if __name__ == "__main__":
    unittest.main()
