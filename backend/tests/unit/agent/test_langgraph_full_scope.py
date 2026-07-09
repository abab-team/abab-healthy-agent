from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_rc02_langgraph.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}")

from app.agent import service as agent_service  # noqa: E402
from app.agent.enums import AgentWorkflowName  # noqa: E402
from app.agent.langgraph.dispatcher import AgentGraphDispatcher  # noqa: E402
from app.agent.langgraph.state import validate_no_sensitive_state  # noqa: E402
from app.agent.runtime import AgentRuntime  # noqa: E402
from app.agent.schemas import AgentRunRequest  # noqa: E402
from app.agent.workflows import AgentWorkflowRegistry, default_workflow_registry  # noqa: E402
from app.agent.workflows.daily_report_workflow import DailyReportWorkflow  # noqa: E402
from app.agent.workflows.document_extract_workflow import DocumentExtractWorkflow  # noqa: E402
from app.agent.workflows.health_knowledge_qa_workflow import HealthKnowledgeQAWorkflow  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402


class LangGraphFullScopeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        engine.dispose()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        self.actor_user_id = uuid4()

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()
        engine.dispose()

    def test_sensitive_state_rejects_rc02_forbidden_keys(self) -> None:
        for key in ("raw_prompt", "raw_llm_response", "current_user_id", "target_user_id_from_llm", "family_id_from_llm", "tool_name", "input_data"):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    validate_no_sensitive_state({key: "unsafe"})

    def test_dispatcher_flags_are_per_workflow(self) -> None:
        settings = Settings(LANGGRAPH_ENABLED=True, LANGGRAPH_DOCUMENT_EXTRACT_ENABLED=True)
        dispatcher = AgentGraphDispatcher(settings)

        self.assertTrue(dispatcher.enabled_for(AgentWorkflowName.DOCUMENT_EXTRACT_WORKFLOW))
        self.assertFalse(dispatcher.enabled_for(AgentWorkflowName.CHAT_WORKFLOW))

    def test_placeholder_workflows_are_registered(self) -> None:
        registry = default_workflow_registry()

        self.assertIsInstance(registry.get(AgentWorkflowName.DOCUMENT_EXTRACT_WORKFLOW), DocumentExtractWorkflow)
        self.assertIsInstance(registry.get(AgentWorkflowName.DAILY_REPORT_WORKFLOW), DailyReportWorkflow)
        self.assertIsInstance(registry.get(AgentWorkflowName.HEALTH_KNOWLEDGE_QA_WORKFLOW), HealthKnowledgeQAWorkflow)

    def test_document_extract_graph_runs_metadata_only_preview(self) -> None:
        settings = Settings(LANGGRAPH_ENABLED=True, LANGGRAPH_DOCUMENT_EXTRACT_ENABLED=True)
        registry = AgentWorkflowRegistry()
        registry.register(DocumentExtractWorkflow(settings=settings))

        result = AgentRuntime(registry).run(
            self.db,
            self._request(
                AgentWorkflowName.DOCUMENT_EXTRACT_WORKFLOW,
                user_message="Please organize this uploaded report.",
                workflow_payload={"file_name": "checkup.pdf", "mime_type": "application/pdf"},
            ),
        )
        joined = self._safety_join(result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertIn("raw_ocr_returned=false", result.generated_content or "")
        self.assertIn("file_path_returned=false", result.generated_content or "")
        self.assertIn("document_extract_graph", joined)
        self.assertIn("document_context_loader", joined)

    def test_daily_report_graph_runs_without_storing_report(self) -> None:
        settings = Settings(LANGGRAPH_ENABLED=True, LANGGRAPH_DAILY_REPORT_ENABLED=True)
        registry = AgentWorkflowRegistry()
        registry.register(DailyReportWorkflow(settings=settings))

        result = AgentRuntime(registry).run(
            self.db,
            self._request(AgentWorkflowName.DAILY_REPORT_WORKFLOW, user_message="Generate today's system record report."),
        )
        joined = self._safety_join(result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertIn("Based on system records only", result.generated_content or "")
        self.assertIn("No stored daily report was created", result.generated_content or "")
        self.assertIn("daily_report_graph", joined)
        self.assertNotIn("tool_name", joined)

    def test_health_knowledge_qa_graph_uses_internal_safe_context_only(self) -> None:
        settings = Settings(LANGGRAPH_ENABLED=True, LANGGRAPH_HEALTH_KNOWLEDGE_QA_ENABLED=True, RAG_ENABLED=False)
        registry = AgentWorkflowRegistry()
        registry.register(HealthKnowledgeQAWorkflow(settings=settings))

        result = AgentRuntime(registry).run(
            self.db,
            self._request(AgentWorkflowName.HEALTH_KNOWLEDGE_QA_WORKFLOW, user_message="What does this record mean?"),
        )
        joined = self._safety_join(result.trace_id)

        self.assertEqual(result.status, "completed")
        self.assertIn("does not use external medical knowledge", result.generated_content or "")
        self.assertIn("health_knowledge_qa_graph", joined)
        self.assertNotIn("raw_prompt", joined)

    def _request(self, workflow_type: AgentWorkflowName, *, user_message: str, workflow_payload: dict | None = None) -> AgentRunRequest:
        return AgentRunRequest(
            actor_user_id=self.actor_user_id,
            target_user_id=self.actor_user_id,
            workflow_type=workflow_type,
            user_message=user_message,
            source="unit-test",
            workflow_payload=workflow_payload,
        )

    def _safety_join(self, trace_id) -> str:  # noqa: ANN001
        trace = agent_service.get_trace(self.db, trace_id)
        checks = agent_service.list_safety_checks(self.db, request_id=trace.request_id)
        return "\n".join(str(check.safety_flags) + str(check.input_risk_summary) + str(check.revised_answer_summary) for check in checks)


if __name__ == "__main__":
    unittest.main()
