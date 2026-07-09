from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_phase19_memory.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")

from app.agent import service as agent_service  # noqa: E402
from app.agent.enums import AgentMemoryStatus, AgentMemoryType  # noqa: E402
from app.agent.memory import service as memory_service  # noqa: E402
from app.agent.models import AgentMemory  # noqa: E402
from app.agent.runtime import AgentRuntime  # noqa: E402
from app.agent.schemas import AgentRunRequest  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.modules.family import service as family_service  # noqa: E402
from app.modules.identity import service as identity_service  # noqa: E402
from app.modules.permissions import service as permissions_service  # noqa: E402


class AgentMemoryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        engine.dispose()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        suffix = uuid4().hex[:8]
        self.actor = identity_service.create_user(
            self.db,
            email=f"phase19.actor.{suffix}@example.com",
            phone=f"p19_actor_{suffix}",
            nickname="Actor",
        )
        self.target = identity_service.create_user(
            self.db,
            email=f"phase19.target.{suffix}@example.com",
            phone=f"p19_target_{suffix}",
            nickname="Target",
        )
        self.family = family_service.create_family_with_owner(
            self.db,
            owner_user_id=self.actor.id,
            family_name="Phase 19 Memory Family",
            owner_display_name="Actor",
        )
        family_service.add_registered_member(
            self.db,
            family_id=self.family.id,
            user_id=self.target.id,
            relationship_label="mother",
            display_name="Mother",
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

    def test_followup_last_month_inherits_previous_metric_and_member(self) -> None:
        session = memory_service.get_or_create_session(db=self.db, user_id=self.actor.id, family_id=self.family.id)
        runtime = AgentRuntime()

        first = runtime.run(
            self.db,
            self._request(
                user_message="爸爸最近一周血压怎么样？",
                target_user_id=self.target.id,
                family_id=self.family.id,
                session_id=str(session.id),
            ),
        )
        second = runtime.run(
            self.db,
            self._request(
                user_message="那上个月呢？",
                target_user_id=self.target.id,
                family_id=self.family.id,
                session_id=str(session.id),
            ),
        )

        first_calls = agent_service.list_tool_calls(self.db, trace_id=first.trace_id)
        second_calls = agent_service.list_tool_calls(self.db, trace_id=second.trace_id)
        messages = memory_service.list_session_messages(self.db, session_id=session.id, user_id=self.actor.id)

        self.assertEqual(first_calls[0].tool_name, "health_data.blood_pressure.summary")
        self.assertEqual(second_calls[0].tool_name, "health_data.blood_pressure.summary")
        self.assertEqual(len(messages), 4)
        self.assertTrue(any(message.time_range_label == "last_month" for message in messages))

    def test_followup_member_inherits_previous_metric_and_time_range(self) -> None:
        session = memory_service.get_or_create_session(db=self.db, user_id=self.actor.id, family_id=self.family.id)
        runtime = AgentRuntime()

        runtime.run(
            self.db,
            self._request(
                user_message="最近 30 天血压记录怎么样？",
                target_user_id=self.actor.id,
                session_id=str(session.id),
            ),
        )
        result = runtime.run(
            self.db,
            self._request(
                user_message="我妈呢？",
                target_user_id=self.target.id,
                family_id=self.family.id,
                session_id=str(session.id),
            ),
        )

        calls = agent_service.list_tool_calls(self.db, trace_id=result.trace_id)
        messages = memory_service.list_session_messages(self.db, session_id=session.id, user_id=self.actor.id)

        self.assertEqual(calls[0].tool_name, "health_data.blood_pressure.summary")
        self.assertTrue(any(message.member_scope == "family" for message in messages))
        self.assertTrue(any(message.time_range_days == 30 for message in messages))

    def test_safe_preference_memory_can_be_listed_and_soft_deleted(self) -> None:
        memory = memory_service.create_safe_preference_memory(
            self.db,
            user_id=self.actor.id,
            family_id=None,
            message="以后回答请简洁一点。",
        )
        self.assertIsNotNone(memory)
        self.assertIsInstance(memory, AgentMemory)
        self.assertEqual(memory.memory_type, AgentMemoryType.USER_PREFERENCE)
        self.assertEqual(len(memory_service.list_memory_items(self.db, user_id=self.actor.id)), 1)

        deleted = memory_service.delete_memory_item(self.db, user_id=self.actor.id, memory_id=memory.id)

        self.assertTrue(deleted)
        self.assertEqual(self.db.get(AgentMemory, memory.id).status, AgentMemoryStatus.DELETED)
        self.assertEqual(memory_service.list_memory_items(self.db, user_id=self.actor.id), [])

    def test_safe_preference_memory_deduplicates_same_active_memory(self) -> None:
        first = memory_service.create_safe_preference_memory(
            self.db,
            user_id=self.actor.id,
            family_id=None,
            message="I prefer short answers from now on.",
        )
        second = memory_service.create_safe_preference_memory(
            self.db,
            user_id=self.actor.id,
            family_id=None,
            message="I prefer short answers from now on.",
        )

        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertEqual(first.id, second.id)
        memories = memory_service.list_memory_items(self.db, user_id=self.actor.id)
        self.assertEqual(len(memories), 1)

    def test_list_memory_items_only_returns_current_user_active_memory(self) -> None:
        actor_memory = memory_service.create_safe_preference_memory(
            self.db,
            user_id=self.actor.id,
            family_id=None,
            message="I prefer short answers from now on.",
        )
        target_memory = memory_service.create_safe_preference_memory(
            self.db,
            user_id=self.target.id,
            family_id=None,
            message="I prefer short answers from now on.",
        )
        self.assertIsNotNone(actor_memory)
        self.assertIsNotNone(target_memory)
        target_memory.status = AgentMemoryStatus.DELETED
        self.db.flush()

        actor_items = memory_service.list_memory_items(self.db, user_id=self.actor.id)
        target_items = memory_service.list_memory_items(self.db, user_id=self.target.id)

        self.assertEqual([item.id for item in actor_items], [actor_memory.id])
        self.assertEqual(target_items, [])

    def test_unsafe_medical_claim_is_not_saved_as_memory(self) -> None:
        memory = memory_service.create_safe_preference_memory(
            self.db,
            user_id=self.actor.id,
            family_id=None,
            message="我确诊了某病，以后不用就医。",
        )

        self.assertIsNone(memory)
        self.assertEqual(memory_service.list_memory_items(self.db, user_id=self.actor.id), [])

    def _request(self, *, user_message: str, target_user_id, family_id=None, session_id: str | None = None) -> AgentRunRequest:
        return AgentRunRequest(
            actor_user_id=self.actor.id,
            target_user_id=target_user_id,
            family_id=family_id,
            workflow_type="chat",
            user_message=user_message,
            source="phase19-unit-test",
            session_id=session_id,
        )


if __name__ == "__main__":
    unittest.main()
