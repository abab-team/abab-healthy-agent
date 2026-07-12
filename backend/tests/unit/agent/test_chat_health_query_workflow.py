from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from uuid import uuid4

TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_phase16_chat_workflow.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")

from app.agent import service as agent_service  # noqa: E402
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
        self.assertIn("sleep_duration", result.generated_content or "")

    def test_chat_daily_status_runs_controlled_readonly_tools(self) -> None:
        health_data_service.add_metric(self.db, user_id=self.actor.id, metric_type="steps", value_numeric=5000, unit="steps")

        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id, "帮我总结最近健康情况"))
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tool_calls_count, 3)
        self.assertEqual(
            [call.tool_name for call in calls],
            ["health_data.metrics.recent", "health_record.symptoms.query", "alerts.query"],
        )

    def test_chat_unknown_intent_does_not_call_tools(self) -> None:
        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id, "tell me a joke"))

        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tool_calls_count, 0)
        self.assertEqual(calls, [])
        self.assertIn("系统内", result.generated_content or "")

    def test_casual_greeting_returns_safe_conversational_response_without_tools(self) -> None:
        result = AgentRuntime().run(self.db, self._request(self.actor.id, self.actor.id, "你好"))

        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tool_calls_count, 0)
        self.assertEqual(calls, [])
        self.assertIn("健康记录整理助手", result.generated_content or "")
        self.assertIn("不替代医生判断", result.generated_content or "")

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

    def test_answer_composer_receives_only_safe_tool_summary_when_enabled(self) -> None:
        class CapturingComposer:
            def __init__(self) -> None:
                self.safe_tool_result_summary = ""
                self.calls = 0

            def compose(self, **kwargs):  # noqa: ANN001
                self.calls += 1
                self.safe_tool_result_summary = kwargs["safe_tool_result_summary"]

                class Result:
                    answer = "根据系统内记录，已整理安全摘要。本回答不替代医生判断。"

                return Result()

        composer = CapturingComposer()
        registry = AgentWorkflowRegistry()
        registry.register(ChatHealthQueryWorkflow(settings=Settings(LLM_ANSWER_COMPOSER_ENABLED=True), answer_composer=composer))

        result = AgentRuntime(registry).run(
            self.db,
            self._request(self.actor.id, self.actor.id, "最近一周我的血压记录"),
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(composer.calls, 1)
        self.assertIn("system", composer.safe_tool_result_summary)
        for term in ("raw_text", "file_path", "raw_extracted_text", "token", "password"):
            self.assertNotIn(term, composer.safe_tool_result_summary.lower())

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


if __name__ == "__main__":
    unittest.main()
