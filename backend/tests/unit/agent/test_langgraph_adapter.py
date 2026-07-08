from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_phase17_langgraph.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")

from app.agent import service as agent_service  # noqa: E402
from app.agent.enums import AgentWorkflowName  # noqa: E402
from app.agent.langgraph import HealthAgentGraphState, LangGraphExecutionAdapter, validate_no_sensitive_state  # noqa: E402
from app.agent.runtime import AgentRuntime  # noqa: E402
from app.agent.schemas import AgentRunRequest  # noqa: E402
from app.agent.workflows import AgentWorkflowRegistry  # noqa: E402
from app.agent.workflows.chat_workflow import ChatHealthQueryWorkflow  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402


class LangGraphAdapterTestCase(unittest.TestCase):
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

    def test_default_settings_keep_langgraph_disabled(self) -> None:
        settings = Settings()
        adapter = LangGraphExecutionAdapter(settings)

        self.assertFalse(settings.LANGGRAPH_ENABLED)
        self.assertFalse(adapter.chat_query_enabled())
        self.assertFalse(adapter.daily_brief_enabled())

    def test_graph_state_rejects_sensitive_keys(self) -> None:
        with self.assertRaises(ValueError):
            validate_no_sensitive_state({"safe": {"raw_text": "should not enter graph state"}})
        with self.assertRaises(ValueError):
            validate_no_sensitive_state({"tool_name": "health_data.metric.summary"})
        with self.assertRaises(ValueError):
            validate_no_sensitive_state({"nested": [{"file_path": "storage://secret"}]})

    def test_graph_state_safe_summary_is_sanitized(self) -> None:
        state = HealthAgentGraphState(
            trace_id=uuid4(),
            request_id="phase17-test",
            workflow_type="chat_workflow",
            actor_user_id=self.actor_user_id,
            target_user_id=self.target_user_id,
            family_id=None,
            user_message_excerpt="sleep summary",
            safety_level="safe",
            intent="query_metrics",
            tool_names=("health_data.metric.summary",),
            node_summary=("input_safety", "parse_intent"),
            metadata={"graph": "chat_health_query_graph"},
        )

        summary = state.safe_summary()

        self.assertEqual(summary["workflow_type"], "chat_workflow")
        self.assertEqual(summary["tool_count"], 1)
        self.assertNotIn("user_message_excerpt", summary)

    def test_chat_graph_records_safe_node_summary_when_enabled(self) -> None:
        settings = Settings(LANGGRAPH_ENABLED=True, LANGGRAPH_CHAT_QUERY_ENABLED=True)
        registry = AgentWorkflowRegistry()
        registry.register(ChatHealthQueryWorkflow(settings=settings))

        result = AgentRuntime(registry).run(
            self.db,
            AgentRunRequest(
                actor_user_id=self.actor_user_id,
                target_user_id=self.target_user_id,
                family_id=None,
                workflow_type=AgentWorkflowName.CHAT_WORKFLOW,
                user_message="hello",
                source="unit-test",
            ),
        )
        trace = agent_service.get_trace(self.db, result.trace_id)
        checks = agent_service.list_safety_checks(self.db, request_id=trace.request_id)
        joined = "\n".join(str(check.safety_flags) + str(check.input_risk_summary) for check in checks)

        self.assertEqual(result.status, "completed")
        self.assertIn("chat_health_query_graph", joined)
        self.assertIn("graph_nodes=input_safety", joined)
        self.assertNotIn("raw_text", joined)
        self.assertNotIn("tool_name", joined)

    def test_graph_disabled_does_not_record_node_summary(self) -> None:
        settings = Settings(LANGGRAPH_ENABLED=False, LANGGRAPH_CHAT_QUERY_ENABLED=True)
        registry = AgentWorkflowRegistry()
        registry.register(ChatHealthQueryWorkflow(settings=settings))

        result = AgentRuntime(registry).run(
            self.db,
            AgentRunRequest(
                actor_user_id=self.actor_user_id,
                target_user_id=self.target_user_id,
                family_id=None,
                workflow_type=AgentWorkflowName.CHAT_WORKFLOW,
                user_message="hello",
                source="unit-test",
            ),
        )
        trace = agent_service.get_trace(self.db, result.trace_id)
        checks = agent_service.list_safety_checks(self.db, request_id=trace.request_id)
        joined = "\n".join(str(check.safety_flags) + str(check.input_risk_summary) for check in checks)

        self.assertEqual(result.status, "completed")
        self.assertNotIn("chat_health_query_graph", joined)


if __name__ == "__main__":
    unittest.main()
