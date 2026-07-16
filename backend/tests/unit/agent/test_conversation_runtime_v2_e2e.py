from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import select


TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_phase_d_v2_e2e.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")

from app.agent import service as agent_service  # noqa: E402
from app.agent.conversation_v2.checkpointer import (  # noqa: E402
    PersistentConversationCheckpointer,
    close_persistent_checkpointer,
)
from app.agent.conversation_v2.service import ConversationRuntimeV2  # noqa: E402
from app.agent.enums import AgentWorkflowName  # noqa: E402
from app.agent.memory import service as memory_service  # noqa: E402
from app.agent.runtime import AgentRuntime  # noqa: E402
from app.agent.schemas import AgentRunRequest  # noqa: E402
from app.agent.workflows import AgentWorkflowRegistry  # noqa: E402
from app.agent.workflows.conversation_runtime_v2 import ConversationRuntimeWorkflow  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.modules.family import service as family_service  # noqa: E402
from app.modules.health_data import service as health_data_service  # noqa: E402
from app.modules.identity import service as identity_service  # noqa: E402
from app.modules.permissions import service as permissions_service  # noqa: E402


class ConversationRuntimeV2EndToEndTestCase(unittest.TestCase):
    """Phase D acceptance tests for the real V2 + ToolExecutor boundary."""

    def setUp(self) -> None:
        engine.dispose()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        suffix = uuid4().hex[:10]
        self.actor = identity_service.create_user(
            self.db,
            email=f"phase.d.actor.{suffix}@example.com",
            phone=f"phase_d_actor_{suffix}",
            nickname="Gala",
        )
        self.father = identity_service.create_user(
            self.db,
            email=f"phase.d.father.{suffix}@example.com",
            phone=f"phase_d_father_{suffix}",
            nickname="爸爸",
        )
        self.family = family_service.create_family_with_owner(
            self.db,
            owner_user_id=self.actor.id,
            family_name="Phase D Family",
            owner_display_name="Gala",
        )
        family_service.add_registered_member(
            self.db,
            family_id=self.family.id,
            user_id=self.father.id,
            relationship_label="爸爸",
            display_name="爸爸",
        )
        permissions_service.create_default_permissions_for_member(
            self.db,
            family_id=self.family.id,
            user_id=self.father.id,
            share_all=True,
        )
        self.session = memory_service.get_or_create_session(
            self.db,
            user_id=self.actor.id,
            family_id=self.family.id,
        )
        self.checkpoint_path = Path(tempfile.gettempdir()) / f"phase_d_v2_{uuid4().hex}.sqlite3"
        self.settings = Settings(
            CONVERSATION_RUNTIME_V2_ENABLED=True,
            CONVERSATION_RUNTIME_V2_CHECKPOINT_PATH=str(self.checkpoint_path),
            CONVERSATION_RUNTIME_V2_MAX_MESSAGES=40,
            LLM_ENABLED=False,
            LLM_CHAT_ENABLED=False,
        )
        self.workflow = ConversationRuntimeWorkflow(settings=self.settings)
        registry = AgentWorkflowRegistry()
        registry.register(self.workflow)
        self.runtime = AgentRuntime(registry=registry)

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()
        engine.dispose()
        close_persistent_checkpointer(self.checkpoint_path)
        self.checkpoint_path.unlink(missing_ok=True)

    def test_chat_continuity_comes_from_checkpoint_messages(self) -> None:
        greeting = self._run("你好")
        identity = self._run("我是谁")
        memory = self._run("你还记得刚才吗")

        messages = self._checkpoint_messages()
        self.assertEqual(greeting.tool_calls_count, 0)
        self.assertIn("Gala", identity.generated_content or "")
        self.assertIn("同一段对话", memory.generated_content or "")
        self.assertEqual([message.type for message in messages], ["system", "human", "ai", "human", "ai", "human", "ai"])

    def test_tool_message_follow_up_reuses_fact_without_new_tool_call(self) -> None:
        health_data_service.add_blood_pressure_record(self.db, user_id=self.actor.id, systolic=118, diastolic=76)

        queried = self._run("查询我的血压")
        interpreted = self._run("这个数值健康吗")
        query_calls = agent_service.list_tool_calls(self.db, trace_id=queried.trace_id)
        follow_up_calls = agent_service.list_tool_calls(self.db, trace_id=interpreted.trace_id)
        messages = self._checkpoint_messages()

        self.assertEqual(queried.tool_calls_count, 1)
        self.assertEqual(query_calls[0].tool_name, "health_data.blood_pressure.summary")
        self.assertEqual(interpreted.tool_calls_count, 0)
        self.assertEqual(follow_up_calls, [])
        self.assertIn("118/76", interpreted.generated_content or "")
        self.assertTrue(any(message.type == "tool" for message in messages))

    def test_family_context_is_rechecked_for_follow_up_tools(self) -> None:
        health_data_service.add_blood_pressure_record(self.db, user_id=self.father.id, systolic=145, diastolic=92)
        health_data_service.add_metric(self.db, user_id=self.father.id, metric_type="sleep_duration", value_numeric=6, unit="hours")

        overview = self._run("查询爸爸最近健康情况")
        blood_pressure = self._run("血压呢")
        interpreted = self._run("这个数值健康吗")
        overview_calls = agent_service.list_tool_calls(self.db, trace_id=overview.trace_id)
        blood_pressure_calls = agent_service.list_tool_calls(self.db, trace_id=blood_pressure.trace_id)

        self.assertGreaterEqual(overview.tool_calls_count, 3)
        self.assertTrue(all(call.target_user_id == self.father.id for call in overview_calls))
        self.assertEqual(blood_pressure.tool_calls_count, 1)
        self.assertEqual(blood_pressure_calls[0].target_user_id, self.father.id)
        self.assertEqual(interpreted.tool_calls_count, 0)
        self.assertIn("145/92", interpreted.generated_content or "")
        context = self._checkpoint_context()
        self.assertEqual(context.get("subject_label"), "爸爸")
        self.assertEqual(context.get("last_fact_type"), "blood_pressure")
        self.assertNotIn("target_user_id", context)

    def test_checkpoint_restores_after_runtime_reinitialization(self) -> None:
        checkpointer = PersistentConversationCheckpointer(self.checkpoint_path)
        first = ConversationRuntimeV2(
            settings=self.settings,
            checkpointer=checkpointer,
            owner_resolver=lambda _: self.actor.id,
            user_context={"name": "Gala"},
        )
        for index in range(12):
            first.run_turn(session_id=self.session.id, user_id=self.actor.id, user_message=f"聊天第 {index} 轮")
        first.close()

        restored_checkpointer = PersistentConversationCheckpointer(self.checkpoint_path)
        restored = ConversationRuntimeV2(
            settings=self.settings,
            checkpointer=restored_checkpointer,
            owner_resolver=lambda _: self.actor.id,
            user_context={"name": "Gala"},
        )
        try:
            result = restored.run_turn(session_id=self.session.id, user_id=self.actor.id, user_message="你还记得刚才吗")
            messages = restored.get_messages(session_id=self.session.id, user_id=self.actor.id)
        finally:
            restored.close()

        self.assertIn("同一段对话", result.answer)
        self.assertEqual(messages[0].type, "system")
        self.assertTrue(any(str(message.content) == "聊天第 11 轮" for message in messages))

    def test_executor_failure_returns_safe_unavailable_message_without_fabrication(self) -> None:
        tool = self.workflow.executor.registry.ensure_tool_allowed("health_data.blood_pressure.summary")
        with patch.object(tool, "execute", side_effect=RuntimeError("database unavailable")):
            result = self._run("查询我的血压")
        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tool_calls_count, 1)
        self.assertEqual(calls[0].status.value, "failed")
        self.assertIn("暂不可用", result.generated_content or "")
        self.assertNotIn("118/76", result.generated_content or "")

    def test_family_permission_isolation_and_record_requests_do_not_enter_draft_flow(self) -> None:
        health_data_service.add_blood_pressure_record(self.db, user_id=self.father.id, systolic=145, diastolic=92)
        permissions_service.update_share_permission(
            self.db,
            actor_user_id=self.actor.id,
            family_id=self.family.id,
            target_user_id=self.father.id,
            updates={"share_all": False, "can_view_metrics": False, "can_view_symptoms": False},
        )

        blocked = self._run("查询爸爸最近健康情况")
        blocked_calls = agent_service.list_tool_calls(self.db, trace_id=blocked.trace_id)
        write_request = self._run("把我的血压改成120/80")

        self.assertTrue(blocked_calls)
        self.assertTrue(any(call.status.value == "blocked_by_permission" for call in blocked_calls))
        self.assertNotIn("145/92", blocked.generated_content or "")
        self.assertEqual(write_request.tool_calls_count, 0)
        self.assertIsNone(write_request.suggested_action)
        self.assertIsNone(write_request.conversation_task)
        self.assertIn("暂时没有开启", write_request.generated_content or "")

    def test_follow_up_time_range_and_record_request_do_not_use_stale_tool_results(self) -> None:
        health_data_service.add_blood_pressure_record(self.db, user_id=self.actor.id, systolic=118, diastolic=76)

        first = self._run("查询我的血压")
        follow_up = self._run("那最近30天呢")
        interpretation = self._run("这个数值怎么样")
        draft = self._run("帮我记录一下今天头晕")
        follow_up_chat = self._run("算了，我不记录了，帮我查天气")

        self.assertEqual(first.tool_calls_count, 1)
        self.assertIn("平均", first.generated_content or "")
        self.assertEqual(follow_up.tool_calls_count, 1)
        follow_up_calls = agent_service.list_tool_calls(self.db, trace_id=follow_up.trace_id)
        self.assertEqual((follow_up_calls[0].input_summary or {}).get("days", {}).get("value"), 30)
        self.assertEqual(interpretation.tool_calls_count, 0)
        self.assertIn("118/76", interpretation.generated_content or "")
        self.assertIsNone(draft.conversation_task)
        self.assertIn("暂时没有开启", draft.generated_content or "")
        self.assertEqual(follow_up_chat.tool_calls_count, 0)
        self.assertIn("天气", follow_up_chat.generated_content or "")
        self.assertNotIn("118/76", follow_up_chat.generated_content or "")

    def _run(self, message: str):
        return self.runtime.run(
            self.db,
            AgentRunRequest(
                actor_user_id=self.actor.id,
                target_user_id=self.actor.id,
                family_id=self.family.id,
                workflow_type=AgentWorkflowName.CHAT_WORKFLOW,
                user_message=message,
                source="phase-d-e2e",
                session_id=str(self.session.id),
            ),
        )

    def _checkpoint_messages(self):
        checkpointer = PersistentConversationCheckpointer(self.checkpoint_path)
        runtime = ConversationRuntimeV2(
            settings=self.settings,
            checkpointer=checkpointer,
            owner_resolver=lambda _: self.actor.id,
        )
        try:
            return runtime.get_messages(session_id=self.session.id, user_id=self.actor.id)
        finally:
            runtime.close()

    def _checkpoint_context(self):
        runtime = ConversationRuntimeV2(
            settings=self.settings,
            checkpointer=PersistentConversationCheckpointer(self.checkpoint_path),
            owner_resolver=lambda _: self.actor.id,
        )
        try:
            state = runtime.graph.get_state({"configurable": {"thread_id": str(self.session.id)}})
            return dict(state.values.get("conversation_context") or {})
        finally:
            runtime.close()


if __name__ == "__main__":
    unittest.main()
