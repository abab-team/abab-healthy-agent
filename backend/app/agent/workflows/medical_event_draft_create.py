from __future__ import annotations

from typing import Any

from app.agent.enums import AgentTraceStatus, AgentWorkflowName
from app.agent.langgraph.dispatcher import AgentGraphDispatcher
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult, ToolExecutionRequest, ToolExecutionResult
from app.agent.tool_executor import AgentToolExecutor
from app.agent.tool_registry import AgentToolRegistry
from app.agent.tools.document_tools import MedicalEventDraftCreateTool
from app.core.config import get_settings
from app.rag.context import safe_rag_context_for_agent


WORKFLOW_TYPE = "medical_event_draft_create"
TOOL_NAME = "document_processing.medical_event_draft.create"
CONFIRMATION_REQUIRED_MESSAGE = "requires_confirmation=true; no draft was created."
BLOCKED_MESSAGE = "Draft workflow was blocked safely. No target data was returned."
COMPLETED_MESSAGE = "Pending medical event draft created from confirmed user input."


class MedicalEventDraftCreateWorkflow:
    workflow_name = AgentWorkflowName.MEDICAL_EVENT_DRAFT_CREATE_WORKFLOW

    def __init__(self, executor: AgentToolExecutor | None = None, *, settings=None) -> None:
        if executor is None:
            registry = AgentToolRegistry()
            registry.register(MedicalEventDraftCreateTool())
            executor = AgentToolExecutor(registry)
        self.executor = executor
        self.settings = settings or get_settings()
        self.graph_dispatcher = AgentGraphDispatcher(self.settings)

    def run(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
        from app.agent.langgraph.graphs.medical_event_draft_graph import MedicalEventDraftGraph

        return self.graph_dispatcher.run_or_fallback(
            context,
            self.workflow_name,
            MedicalEventDraftGraph(executor=self.executor),
            lambda: _workflow_result(
                self.executor.execute(
                    context.db,
                    ToolExecutionRequest(
                        trace_id=context.trace_id,
                        tool_name=TOOL_NAME,
                        actor_user_id=context.request.actor_user_id,
                        target_user_id=context.request.target_user_id,
                        family_id=context.request.family_id,
                        input_data=_tool_input(context),
                        confirmed=context.request.confirmation,
                        safety_level=context.safety_level,
                        reason=WORKFLOW_TYPE,
                    ),
                )
            ),
        )


def _tool_input(context: AgentWorkflowContext) -> dict[str, Any]:
    payload = dict(context.request.workflow_payload or {})
    if not payload.get("summary") and not payload.get("draft_json") and not payload.get("extraction_result_id"):
        payload["summary"] = context.request.user_message
    _attach_safe_rag_hints(context, payload)
    return payload


def _attach_safe_rag_hints(context: AgentWorkflowContext, payload: dict[str, Any]) -> None:
    query = " ".join(
        str(item)
        for item in (
            payload.get("draft_title"),
            payload.get("title"),
            payload.get("summary"),
            context.request.user_message,
        )
        if item
    )
    _, lines, fallback_reason = safe_rag_context_for_agent(
        context.db,
        current_user_id=context.request.actor_user_id,
        target_user_id=context.request.target_user_id,
        family_id=context.request.family_id,
        query=query or "medical event draft related internal records",
        source_types=[
            "medical_document_metadata",
            "document_extraction_preview",
            "medical_event_summary",
            "medical_event_draft_summary",
        ],
        top_k=3,
    )
    if not lines:
        if fallback_reason and fallback_reason != "rag_disabled":
            payload.setdefault("structured_hints", {})["rag_fallback_reason"] = fallback_reason
        return
    hints = payload.setdefault("structured_hints", {})
    if isinstance(hints, dict):
        hints["rag_sources"] = lines


def _workflow_result(tool_result: ToolExecutionResult) -> AgentWorkflowResult:
    if tool_result.requires_confirmation:
        return AgentWorkflowResult(
            message=CONFIRMATION_REQUIRED_MESSAGE,
            generated_content=CONFIRMATION_REQUIRED_MESSAGE,
            status=AgentTraceStatus.BLOCKED,
            tool_calls_count=1,
        )
    if tool_result.blocked or tool_result.status != "completed":
        return AgentWorkflowResult(
            message=BLOCKED_MESSAGE,
            generated_content=BLOCKED_MESSAGE,
            status=AgentTraceStatus.BLOCKED,
            tool_calls_count=1,
        )
    output = tool_result.output_data or {}
    draft_id = str(output.get("draft_id") or "")
    status = str(output.get("status") or "pending")
    content = f"{COMPLETED_MESSAGE} draft_id={draft_id}; status={status}; formal_event_created=false."
    return AgentWorkflowResult(
        message=COMPLETED_MESSAGE,
        generated_content=content,
        status=AgentTraceStatus.SUCCESS,
        tool_calls_count=1,
    )
