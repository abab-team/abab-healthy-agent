from __future__ import annotations

from typing import Protocol

from app.agent.enums import AgentWorkflowName
from app.agent.exceptions import AgentWorkflowNotRegisteredError
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult
from app.agent.workflows.alert_create import AlertCreateWorkflow
from app.agent.workflows.conversation_runtime_v2 import ConversationRuntimeWorkflow
from app.agent.workflows.daily_health_brief import DailyHealthBriefWorkflow
from app.agent.workflows.daily_report_workflow import DailyReportWorkflow
from app.agent.workflows.document_extract_workflow import DocumentExtractWorkflow
from app.agent.workflows.doctor_visit_summary_workflow import DoctorVisitSummaryWorkflow
from app.agent.workflows.free_text_record_workflow import FreeTextRecordWorkflow
from app.agent.workflows.health_knowledge_qa_workflow import HealthKnowledgeQAWorkflow
from app.agent.workflows.medical_event_draft_create import MedicalEventDraftCreateWorkflow
from app.agent.workflows.symptom_draft_create import SymptomDraftCreateWorkflow


NO_OP_AGENT_MESSAGE = "Agent runtime is ready. No AI workflow has been executed in this phase."


class AgentWorkflowHandler(Protocol):
    workflow_name: AgentWorkflowName

    def run(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
        ...


class NoOpHealthAssistantWorkflow:
    workflow_name = AgentWorkflowName.CHAT_WORKFLOW

    def run(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
        return AgentWorkflowResult(
            message=NO_OP_AGENT_MESSAGE,
            generated_content=NO_OP_AGENT_MESSAGE,
            tool_calls_count=0,
        )


class AgentWorkflowRegistry:
    def __init__(self) -> None:
        self._handlers: dict[AgentWorkflowName, AgentWorkflowHandler] = {}

    def register(self, handler: AgentWorkflowHandler) -> None:
        self._handlers[handler.workflow_name] = handler

    def get(self, workflow_name: AgentWorkflowName) -> AgentWorkflowHandler:
        handler = self._handlers.get(workflow_name)
        if handler is None:
            raise AgentWorkflowNotRegisteredError("workflow handler is not registered")
        return handler


def default_workflow_registry() -> AgentWorkflowRegistry:
    registry = AgentWorkflowRegistry()
    registry.register(ConversationRuntimeWorkflow())
    registry.register(DailyHealthBriefWorkflow())
    registry.register(FreeTextRecordWorkflow())
    registry.register(DoctorVisitSummaryWorkflow())
    registry.register(DocumentExtractWorkflow())
    registry.register(DailyReportWorkflow())
    registry.register(HealthKnowledgeQAWorkflow())
    registry.register(SymptomDraftCreateWorkflow())
    registry.register(MedicalEventDraftCreateWorkflow())
    registry.register(AlertCreateWorkflow())
    return registry
