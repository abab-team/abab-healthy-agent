from __future__ import annotations

from collections.abc import Callable

from app.agent.enums import AgentWorkflowName
from app.agent.langgraph.registry import AgentGraphRunner
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult
from app.core.config import get_settings


WORKFLOW_FLAG_BY_NAME = {
    AgentWorkflowName.CHAT_WORKFLOW: "LANGGRAPH_CHAT_QUERY_ENABLED",
    AgentWorkflowName.FREE_TEXT_RECORD_WORKFLOW: "LANGGRAPH_FREE_TEXT_RECORD_ENABLED",
    AgentWorkflowName.DOCTOR_VISIT_SUMMARY_WORKFLOW: "LANGGRAPH_DOCTOR_VISIT_SUMMARY_ENABLED",
    AgentWorkflowName.DOCUMENT_EXTRACT_WORKFLOW: "LANGGRAPH_DOCUMENT_EXTRACT_ENABLED",
    AgentWorkflowName.DAILY_REPORT_WORKFLOW: "LANGGRAPH_DAILY_REPORT_ENABLED",
    AgentWorkflowName.HEALTH_KNOWLEDGE_QA_WORKFLOW: "LANGGRAPH_HEALTH_KNOWLEDGE_QA_ENABLED",
    AgentWorkflowName.ALERT_CREATE_WORKFLOW: "LANGGRAPH_ALERT_CREATE_ENABLED",
    AgentWorkflowName.SYMPTOM_DRAFT_CREATE_WORKFLOW: "LANGGRAPH_SYMPTOM_DRAFT_CREATE_ENABLED",
    AgentWorkflowName.MEDICAL_EVENT_DRAFT_CREATE_WORKFLOW: "LANGGRAPH_MEDICAL_EVENT_DRAFT_CREATE_ENABLED",
    AgentWorkflowName.DAILY_HEALTH_BRIEF: "LANGGRAPH_DAILY_BRIEF_ENABLED",
}


class AgentGraphDispatcher:
    def __init__(self, settings=None) -> None:
        self.settings = settings or get_settings()

    def enabled_for(self, workflow_name: AgentWorkflowName) -> bool:
        if not getattr(self.settings, "LANGGRAPH_ENABLED", False):
            return False
        flag_name = WORKFLOW_FLAG_BY_NAME.get(workflow_name)
        return bool(flag_name and getattr(self.settings, flag_name, False))

    def run_or_fallback(
        self,
        context: AgentWorkflowContext,
        workflow_name: AgentWorkflowName,
        graph: AgentGraphRunner,
        fallback: Callable[[], AgentWorkflowResult],
    ) -> AgentWorkflowResult:
        if not self.enabled_for(workflow_name):
            return fallback()
        try:
            return graph.run(context).result
        except Exception:
            if getattr(self.settings, "LANGGRAPH_STRICT_MODE", False):
                raise
            return fallback()
