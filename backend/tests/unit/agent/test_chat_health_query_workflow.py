from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_phase16_chat_workflow.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")

from app.agent import service as agent_service  # noqa: E402
from app.agent.memory import service as memory_service  # noqa: E402
from app.agent.models import AgentConversationTask  # noqa: E402
from app.agent.enums import AgentTraceStatus, AgentWorkflowName  # noqa: E402
from app.agent.runtime import AgentRuntime  # noqa: E402
from app.agent.schemas import AgentRunRequest  # noqa: E402
from app.agent.workflows import AgentWorkflowRegistry  # noqa: E402
from app.agent.workflows.chat_workflow import ChatHealthQueryWorkflow  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.modules.document_center import service as document_service  # noqa: E402
from app.modules.document_center.enums import DocumentType  # noqa: E402
from app.modules.family import service as family_service  # noqa: E402
from app.modules.health_data import service as health_data_service  # noqa: E402
from app.modules.health_record import service as health_record_service  # noqa: E402
from app.modules.identity import service as identity_service  # noqa: E402
from app.modules.permissions import service as permissions_service  # noqa: E402


UNSAFE_TERMS = (
    "diagnosis",
    "prescription",
    "dosage",
    "stop medication",
    "file_path",
    "raw_extracted_text",
    "password",
    "token",
    "api_key",
    "private symptom text",
    "storage://",
)


class ChatHealthQueryWorkflowTestCase(unittest.TestCase):
    def setUp(self) -> None:
        engine.dispose()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        suffix = uuid4().hex[:8]
        self.actor = identity_service.create_user(
            self.db,
            email=f"phase16.chat.actor.{suffix}@example.com",
            phone=f"p16chat_actor_{suffix}",
            nickname="Actor",
        )
        self.target = identity_service.create_user(
            self.db,
            email=f"phase16.chat.target.{suffix}@example.com",
            phone=f"p16chat_target_{suffix}",
            nickname="Target",
        )
        self.family = family_service.create_family_with_owner(
            self.db,
            owner_user_id=self.actor.id,
            family_name="Phase 16 Chat Family",
            owner_display_name="Actor",
        )
        family_service.add_registered_member(
            self.db,
            family_id=self.family.id,
            user_id=self.target.id,
            relationship_label="爸爸",
            display_name="爸爸",
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

    def test_chat_query_sleep_metric_runs_one_tool(self) -> None:
        health_data_service.add_metric(
            self.db,
            user_id=self.actor.id,
            metric_type="sleep_duration",
            value_numeric=7.5,
            unit="hours",
        )

        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id, "最近一周我的睡眠记录怎么样？"))
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.workflow_type, "chat_workflow")
        self.assertEqual(result.tool_calls_count, 1)
        self.assertEqual(calls[0].tool_name, "health_data.metric.summary")
        self.assertIn("根据系统内记录", result.generated_content or "")
        self.assertIn("睡眠", result.generated_content or "")

    def test_chat_daily_status_runs_controlled_readonly_tools(self) -> None:
        health_data_service.add_metric(self.db, user_id=self.actor.id, metric_type="steps", value_numeric=5000, unit="steps")

        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id, "帮我总结最近健康情况"))
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tool_calls_count, 6)
        self.assertEqual(
            [call.tool_name for call in calls],
            [
                "health_data.metrics.recent",
                "health_data.blood_pressure.summary",
                "health_record.symptoms.query",
                "documents.query",
                "medical_timeline.events.query",
                "alerts.query",
            ],
        )

    def test_family_overview_uses_controlled_tools_for_multiple_record_categories(self) -> None:
        health_data_service.add_blood_pressure_record(
            self.db,
            user_id=self.target.id,
            systolic=120,
            diastolic=78,
        )
        health_data_service.add_metric(
            self.db,
            user_id=self.target.id,
            metric_type="steps",
            value_numeric=5600,
            unit="steps",
        )

        result = AgentRuntime().run(
            self.db,
            self._request(self.actor.id, self.actor.id, "爸爸最近健康情况怎么样？", family_id=self.family.id),
        )
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tool_calls_count, 6)
        self.assertTrue(all(call.target_user_id == self.target.id for call in calls))
        self.assertIn("爸爸", result.generated_content or "")
        self.assertIn("健康指标", result.generated_content or "")
        self.assertIn("血压记录", result.generated_content or "")
        self.assertIn("文档资料", result.generated_content or "")

    def test_family_overview_lists_available_metric_categories_without_agent_db_access(self) -> None:
        health_data_service.add_metric(self.db, user_id=self.target.id, metric_type="sleep_duration", value_numeric=6.8, unit="hours")
        health_data_service.add_metric(self.db, user_id=self.target.id, metric_type="steps", value_numeric=5600, unit="steps")
        health_data_service.add_metric(self.db, user_id=self.target.id, metric_type="weight", value_numeric=68.2, unit="kg")

        result = AgentRuntime().run(
            self.db,
            self._request(self.actor.id, self.actor.id, "爸爸最近健康情况怎么样？", family_id=self.family.id),
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tool_calls_count, 6)
        self.assertIn("睡眠", result.generated_content or "")
        self.assertIn("步数", result.generated_content or "")
        self.assertIn("体重", result.generated_content or "")

    def test_medical_history_query_uses_permission_gated_safe_summaries(self) -> None:
        from app.modules.health_profile import service as health_profile_service
        from app.modules.medical_timeline import service as medical_timeline_service

        health_profile_service.update_profile_summaries(
            self.db,
            user_id=self.target.id,
            allergy_summary="已由用户确认的过敏资料",
            medication_summary="已保存的用药资料",
        )
        medical_timeline_service.create_medical_event(
            self.db,
            user_id=self.target.id,
            family_id=self.family.id,
            created_by_user_id=self.target.id,
            event_type="follow_up",
            title="复查记录",
        )

        result = AgentRuntime().run(
            self.db,
            self._request(self.actor.id, self.actor.id, "爸爸有什么过敏记录？", family_id=self.family.id),
        )
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tool_calls_count, 3)
        self.assertEqual([call.tool_name for call in calls], ["health_profile.get", "medical_timeline.events.query", "documents.query"])
        self.assertIn("过敏资料摘要", result.generated_content or "")
        self.assertNotIn("已由用户确认的过敏资料", result.generated_content or "")

    def test_casual_chat_does_not_call_tools(self) -> None:
        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id, "tell me a joke"))

        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tool_calls_count, 0)
        self.assertEqual(calls, [])
        self.assertNotIn("系统内已有记录", result.generated_content or "")

    def test_casual_greeting_returns_safe_conversational_response_without_tools(self) -> None:
        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id, "你好"))

        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tool_calls_count, 0)
        self.assertEqual(calls, [])
        self.assertIn("你好", result.generated_content or "")
        self.assertNotIn("不替代医生判断", result.generated_content or "")

    def test_health_knowledge_uses_no_personal_data_tools(self) -> None:
        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id, "为什么会睡不好？"))
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tool_calls_count, 0)
        self.assertEqual(calls, [])
        self.assertIn("睡眠", result.generated_content or "")

    def test_write_request_only_returns_a_draft_entry_suggestion(self) -> None:
        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id, "帮我记录今天头痛"))
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tool_calls_count, 0)
        self.assertEqual(result.suggested_action, "symptom_draft")
        self.assertEqual(calls, [])
        self.assertIn("预览不会写入", result.generated_content or "")

    def test_record_follow_up_resumes_only_a_controlled_draft_navigation(self) -> None:
        session = memory_service.get_or_create_session(
            self.db,
            user_id=self.actor.id,
            family_id=self.family.id,
            title="健康记录草稿",
        )
        first = self._request(self.actor.id, self.actor.id, "帮我记录体温36度", family_id=self.family.id)
        first = AgentRunRequest(**{**first.__dict__, "session_id": str(session.id)})
        initial = AgentRuntime().run(self.db, first)

        follow_up = self._request(self.actor.id, self.actor.id, "整理", family_id=self.family.id)
        follow_up = AgentRunRequest(**{**follow_up.__dict__, "session_id": str(session.id)})
        result = AgentRuntime().run(self.db, follow_up)
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(initial.suggested_action, "health_event_draft")
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.suggested_action, "health_event_draft")
        self.assertEqual(result.tool_calls_count, 0)
        self.assertEqual(calls, [])
        self.assertIn("预览不会写入", result.generated_content or "")

    def test_symptom_task_state_continues_before_router_and_never_writes_health_record(self) -> None:
        session = memory_service.get_or_create_session(
            self.db,
            user_id=self.actor.id,
            family_id=self.family.id,
            title="symptom task",
        )

        initial = AgentRuntime().run(
            self.db,
            self._request_with_session("\u8bb0\u5f55\u4e00\u4e0b\u6211\u5934\u6655", session_id=session.id),
        )
        started = self.db.scalar(
            select(AgentConversationTask).where(AgentConversationTask.session_id == session.id)
        )
        self.assertEqual(initial.tool_calls_count, 0)
        self.assertEqual(initial.conversation_task["status"], "collecting")
        self.assertEqual(initial.conversation_task["missing_fields"], ["start_time", "duration"])
        self.assertIsNotNone(started)

        began = AgentRuntime().run(self.db, self._request_with_session("\u521a\u624d\u5f00\u59cb\u7684", session_id=session.id))
        self.assertEqual(began.conversation_task["missing_fields"], ["duration"])

        duration = AgentRuntime().run(self.db, self._request_with_session("\u6301\u7eed10\u5206\u949f", session_id=session.id))
        self.assertEqual(duration.conversation_task["missing_fields"], [])

        organized = AgentRuntime().run(self.db, self._request_with_session("\u6574\u7406\u4e00\u4e0b", session_id=session.id))
        self.assertEqual(organized.conversation_task["status"], "ready_for_preview")
        self.assertEqual(organized.suggested_action, "symptom_draft")

        confirmed = AgentRuntime().run(self.db, self._request_with_session("\u786e\u8ba4", session_id=session.id))
        self.assertEqual(confirmed.conversation_task["status"], "awaiting_confirmation")
        self.assertEqual(confirmed.suggested_action, "symptom_draft")
        self.assertEqual(confirmed.tool_calls_count, 0)
        self.assertEqual(agent_service.list_tool_calls(self.db, trace_id=confirmed.trace_id), [])

    def test_temperature_task_can_be_organized_as_controlled_health_event_draft(self) -> None:
        session = memory_service.get_or_create_session(self.db, user_id=self.actor.id, family_id=self.family.id)
        initial = AgentRuntime().run(
            self.db,
            self._request_with_session("\u8bb0\u5f55\u4f53\u6e2936\u5ea6", session_id=session.id),
        )
        organized = AgentRuntime().run(self.db, self._request_with_session("\u6574\u7406", session_id=session.id))

        self.assertEqual(initial.conversation_task["task_type"], "health_event_draft")
        self.assertEqual(organized.conversation_task["status"], "ready_for_preview")
        self.assertEqual(organized.suggested_action, "health_event_draft")
        self.assertEqual(organized.tool_calls_count, 0)

    def test_casual_chat_never_creates_conversation_task_or_calls_tools(self) -> None:
        session = memory_service.get_or_create_session(self.db, user_id=self.actor.id, family_id=self.family.id)
        for message in ("\u4f60\u597d", "\u4f60\u662f\u8c01", "\u8c22\u8c22", "\u4eca\u5929\u600e\u4e48\u6837"):
            result = AgentRuntime().run(self.db, self._request_with_session(message, session_id=session.id))
            self.assertEqual(result.status, "completed")
            self.assertEqual(result.tool_calls_count, 0)
            self.assertIsNone(result.conversation_task)

        self.assertEqual(
            self.db.scalars(select(AgentConversationTask).where(AgentConversationTask.session_id == session.id)).all(),
            [],
        )

    def test_rule_matched_query_does_not_call_llm_planner(self) -> None:
        class RaisingPlanner:
            def plan(self, **kwargs):  # noqa: ANN001
                raise AssertionError("planner should not run for rule-matched queries")

        registry = AgentWorkflowRegistry()
        registry.register(
            ChatHealthQueryWorkflow(
                settings=Settings(LLM_PLANNER_ENABLED=True),
                planner_service=RaisingPlanner(),
            )
        )

        result = AgentRuntime(registry).run(
            self.db,
            self._request(self.actor.id, self.actor.id, "最近一周我的血压记录"),
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tool_calls_count, 1)

    def test_unknown_query_can_use_controlled_llm_planner(self) -> None:
        registry = AgentWorkflowRegistry()
        registry.register(
            ChatHealthQueryWorkflow(
                settings=Settings(LLM_PLANNER_ENABLED=True, LLM_ENABLED=True, LLM_PROVIDER="mock"),
            )
        )

        result = AgentRuntime(registry).run(self.db, self._request(self.actor.id, self.actor.id, "pressure readings please"))
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tool_calls_count, 1)
        self.assertEqual(calls[0].tool_name, "health_data.blood_pressure.summary")

    def test_health_insight_responder_receives_only_safe_facts(self) -> None:
        class CapturingResponder:
            def __init__(self) -> None:
                self.safe_facts = ""
                self.calls = 0

            def respond(self, **kwargs):  # noqa: ANN001
                self.calls += 1
                self.safe_facts = kwargs["safe_facts"]
                return kwargs["fallback_answer"]

        responder = CapturingResponder()
        health_data_service.add_blood_pressure_record(
            self.db,
            user_id=self.actor.id,
            systolic=118,
            diastolic=76,
        )
        registry = AgentWorkflowRegistry()
        registry.register(ChatHealthQueryWorkflow(settings=Settings(LLM_ENABLED=False), conversation_responder=responder))

        result = AgentRuntime(registry).run(
            self.db,
            self._request(self.actor.id, self.actor.id, "最近一周我的血压记录"),
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(responder.calls, 1)
        self.assertIn("血压", responder.safe_facts)
        for term in ("raw_text", "file_path", "raw_extracted_text", "token", "password"):
            self.assertNotIn(term, responder.safe_facts.lower())

    def test_chat_documents_query_does_not_leak_file_path(self) -> None:
        document_service.create_document_metadata(
            self.db,
            user_id=self.actor.id,
            uploaded_by_user_id=self.actor.id,
            document_type=DocumentType.CHECKUP_REPORT,
            title="年度检查资料",
            file_name="checkup.pdf",
            file_path="storage://private/checkup.pdf",
        )

        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id, "系统内有哪些文档资料？"))
        content = (result.generated_content or "").lower()

        self.assertEqual(result.status, "completed")
        self.assertIn("文档资料", result.generated_content or "")
        for term in UNSAFE_TERMS:
            self.assertNotIn(term, content)

    def test_family_permission_denied_returns_partial_unavailable_without_target_data(self) -> None:
        health_record_service.create_symptom_record(
            self.db,
            user_id=self.target.id,
            family_id=self.family.id,
            created_by_user_id=self.actor.id,
            raw_text="private symptom text",
            symptom_name="headache",
        )
        permissions_service.update_share_permission(
            self.db,
            actor_user_id=self.actor.id,
            family_id=self.family.id,
            target_user_id=self.target.id,
            updates={"share_all": False, "can_view_symptoms": False},
        )

        result = AgentRuntime().run(
            self.db,
            self._request(self.actor.id, self.target.id, "看看家人的症状记录", family_id=self.family.id),
        )
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertEqual(calls[0].status.value, "blocked_by_permission")
        self.assertIn("部分信息因权限设置暂不可用", result.generated_content or "")
        self.assertNotIn("private symptom text", result.generated_content or "")

    def test_family_query_resolves_member_before_permission_checked_tool_execution(self) -> None:
        health_data_service.add_blood_pressure_record(
            self.db,
            user_id=self.target.id,
            systolic=120,
            diastolic=78,
        )

        result = AgentRuntime().run(
            self.db,
            self._request(self.actor.id, self.actor.id, "爸爸最近血压怎么样？", family_id=self.family.id),
        )
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tool_calls_count, 1)
        self.assertEqual(calls[0].target_user_id, self.target.id)
        self.assertIn("爸爸", result.generated_content or "")
        self.assertIn("120/78", result.generated_content or "")

    def test_follow_up_reuses_member_metric_and_changes_time_range(self) -> None:
        health_data_service.add_blood_pressure_record(
            self.db,
            user_id=self.target.id,
            systolic=120,
            diastolic=78,
        )
        session = memory_service.get_or_create_session(
            self.db,
            user_id=self.actor.id,
            family_id=self.family.id,
            title="爸爸血压",
        )
        first = self._request(self.actor.id, self.actor.id, "爸爸最近血压怎么样？", family_id=self.family.id)
        first = AgentRunRequest(**{**first.__dict__, "session_id": str(session.id)})
        AgentRuntime().run(self.db, first)
        follow_up = self._request(self.actor.id, self.actor.id, "那上个月呢？", family_id=self.family.id)
        follow_up = AgentRunRequest(**{**follow_up.__dict__, "session_id": str(session.id)})
        result = AgentRuntime().run(self.db, follow_up)
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertEqual(calls[0].target_user_id, self.target.id)
        self.assertIn("爸爸", result.generated_content or "")

    def test_family_overview_then_metric_then_last_month_preserves_member_context(self) -> None:
        health_data_service.add_blood_pressure_record(
            self.db,
            user_id=self.target.id,
            systolic=120,
            diastolic=78,
        )
        session = memory_service.get_or_create_session(
            self.db,
            user_id=self.actor.id,
            family_id=self.family.id,
            title="爸爸健康概览",
        )

        overview = AgentRuntime().run(
            self.db,
            self._request_with_session("爸爸最近怎么样？", session_id=session.id),
        )
        metric = AgentRuntime().run(
            self.db,
            self._request_with_session("那血压呢？", session_id=session.id),
        )
        last_month = AgentRuntime().run(
            self.db,
            self._request_with_session("上个月呢？", session_id=session.id),
        )

        metric_calls = agent_service.list_tool_calls(self.db, trace_id=metric.trace_id)
        last_month_calls = agent_service.list_tool_calls(self.db, trace_id=last_month.trace_id)
        self.assertEqual(overview.tool_calls_count, 6)
        self.assertEqual(metric.tool_calls_count, 1)
        self.assertEqual(metric_calls[0].tool_name, "health_data.blood_pressure.summary")
        self.assertEqual(metric_calls[0].target_user_id, self.target.id)
        self.assertEqual(last_month_calls[0].tool_name, "health_data.blood_pressure.summary")
        self.assertEqual(last_month_calls[0].target_user_id, self.target.id)

    def test_trace_does_not_remain_running(self) -> None:
        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id, "最近一周血压记录"))
        trace = agent_service.get_trace(self.db, result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertNotEqual(trace.status, AgentTraceStatus.RUNNING)

    def _request(self, actor_user_id, target_user_id, user_message: str, *, family_id=None) -> AgentRunRequest:
        return AgentRunRequest(
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            family_id=family_id,
            workflow_type=AgentWorkflowName.CHAT_WORKFLOW,
            user_message=user_message,
            source="unit-test",
        )

    def _request_with_session(self, user_message: str, *, session_id) -> AgentRunRequest:
        return AgentRunRequest(
            actor_user_id=self.actor.id,
            target_user_id=self.actor.id,
            family_id=self.family.id,
            workflow_type=AgentWorkflowName.CHAT_WORKFLOW,
            user_message=user_message,
            source="unit-test",
            session_id=str(session_id),
        )


    def test_current_user_recent_data_runs_controlled_overview_tools(self) -> None:
        health_data_service.add_metric(self.db, user_id=self.actor.id, metric_type="steps", value_numeric=5000, unit="steps")

        result = AgentRuntime().run(
            self.db,
            self._request(self.actor.id, self.actor.id, "\u67e5\u8be2\u6211\u6700\u8fd1\u7684\u6570\u636e"),
        )
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tool_calls_count, 6)
        self.assertEqual(calls[0].tool_name, "health_data.metrics.recent")

    def test_new_health_question_pauses_active_task_instead_of_being_swallowed(self) -> None:
        session = memory_service.get_or_create_session(self.db, user_id=self.actor.id, family_id=self.family.id)

        started = AgentRuntime().run(self.db, self._request_with_session("\u8bb0\u5f55\u4e00\u4e0b\u6211\u7684\u4f53\u6e2936\u5ea6", session_id=session.id))
        interrupted = AgentRuntime().run(self.db, self._request_with_session("\u6211\u5065\u5eb7\u5417", session_id=session.id))
        task = self.db.scalar(select(AgentConversationTask).where(AgentConversationTask.session_id == session.id))

        self.assertEqual(started.conversation_task["status"], "collecting")
        self.assertEqual(interrupted.tool_calls_count, 0)
        self.assertIsNone(interrupted.suggested_action)
        self.assertIsNotNone(task)
        self.assertEqual(task.status, "paused")
        self.assertNotIn("\u6574\u7406\u4e00\u4e0b", interrupted.generated_content or "")

        resumed = AgentRuntime().run(self.db, self._request_with_session("\u6574\u7406\u4e00\u4e0b", session_id=session.id))
        self.assertEqual(resumed.suggested_action, "health_event_draft")
        self.assertEqual(task.status, "ready_for_preview")

    def test_family_overview_expansion_keeps_member_and_uses_all_overview_tools(self) -> None:
        health_data_service.add_blood_pressure_record(self.db, user_id=self.target.id, systolic=120, diastolic=78)
        session = memory_service.get_or_create_session(self.db, user_id=self.actor.id, family_id=self.family.id)

        AgentRuntime().run(self.db, self._request_with_session("\u67e5\u8be2\u7238\u7238\u5065\u5eb7\u60c5\u51b5", session_id=session.id))
        expanded = AgentRuntime().run(self.db, self._request_with_session("\u4e0d\u53ea\u662f\u8840\u538b", session_id=session.id))
        calls = agent_service.list_tool_calls(self.db, trace_id=expanded.trace_id)

        self.assertEqual(expanded.tool_calls_count, 6)
        self.assertTrue(all(call.target_user_id == self.target.id for call in calls))
        self.assertIn("\u7238\u7238", expanded.generated_content or "")

    def test_relative_blood_pressure_interpretation_requeries_authorized_fact(self) -> None:
        health_data_service.add_blood_pressure_record(self.db, user_id=self.actor.id, systolic=118, diastolic=76)
        session = memory_service.get_or_create_session(self.db, user_id=self.actor.id, family_id=self.family.id)

        AgentRuntime().run(self.db, self._request_with_session("\u67e5\u8be2\u8840\u538b", session_id=session.id))
        interpreted = AgentRuntime().run(self.db, self._request_with_session("\u8fd9\u4e2a\u6570\u503c\u5065\u5eb7\u5417", session_id=session.id))
        calls = agent_service.list_tool_calls(self.db, trace_id=interpreted.trace_id)

        self.assertEqual(interpreted.tool_calls_count, 1)
        self.assertEqual(calls[0].tool_name, "health_data.blood_pressure.summary")
        self.assertIn("\u5e38\u89c1\u6210\u4eba\u9759\u606f\u8840\u538b\u53c2\u8003\u533a\u95f4", interpreted.generated_content or "")
        self.assertNotIn("\u8bca\u65ad", interpreted.generated_content or "")

    def test_cold_knowledge_reply_stays_within_non_treatment_boundary(self) -> None:
        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id, "\u611f\u5192\u600e\u4e48\u529e"))

        self.assertEqual(result.tool_calls_count, 0)
        self.assertNotIn("\u5904\u65b9", result.generated_content or "")
        self.assertNotIn("\u5242\u91cf", result.generated_content or "")
        self.assertNotIn("\u505c\u836f", result.generated_content or "")


if __name__ == "__main__":
    unittest.main()
