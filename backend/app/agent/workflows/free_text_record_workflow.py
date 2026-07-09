from __future__ import annotations

from typing import Any

from app.agent.enums import AgentTraceStatus, AgentWorkflowName
from app.agent.langgraph.dispatcher import AgentGraphDispatcher
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult, ToolExecutionRequest, ToolExecutionResult
from app.agent.tool_executor import AgentToolExecutor
from app.agent.tool_registry import AgentToolRegistry
from app.agent.tools.health_record_tools import SymptomDraftCreateTool
from app.core.config import get_settings


WORKFLOW_TYPE = "free_text_record_workflow"
TOOL_NAME = "health_record.symptom_draft.create"
PREVIEW_MESSAGE = "Preview only. No formal record or draft was created."
BLOCKED_MESSAGE = "Free text record workflow was blocked safely. No target data was returned."
COMPLETED_MESSAGE = "Pending free text health note draft created from confirmed user input."


class FreeTextRecordWorkflow:
    workflow_name = AgentWorkflowName.FREE_TEXT_RECORD_WORKFLOW

    def __init__(self, executor: AgentToolExecutor | None = None, *, settings=None) -> None:
        if executor is None:
            registry = AgentToolRegistry()
            registry.register(SymptomDraftCreateTool())
            executor = AgentToolExecutor(registry)
        self.executor = executor
        self.settings = settings or get_settings()
        self.graph_dispatcher = AgentGraphDispatcher(self.settings)

    def run(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
        from app.agent.langgraph.graphs.free_text_record_graph import FreeTextRecordGraph

        return self.graph_dispatcher.run_or_fallback(
            context,
            self.workflow_name,
            FreeTextRecordGraph(executor=self.executor),
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
    payload.setdefault("raw_text", context.request.user_message)
    extracted_json = dict(payload.get("extracted_json") or {})
    extracted_json.setdefault("source", WORKFLOW_TYPE)
    extracted_json.setdefault("draft_kind", "free_text_health_note")
    extracted_json.setdefault("safety_boundary", "pending_draft_only")
    payload["extracted_json"] = extracted_json
    return payload


def _workflow_result(tool_result: ToolExecutionResult) -> AgentWorkflowResult:
    if tool_result.requires_confirmation:
        content = (
            "Based on system records only, this is a preview for a pending health note draft. "
            "No formal health fact was created. Confirm only if you want to create a pending draft for later review. "
            "This does not replace a doctor's judgment."
        )
        return AgentWorkflowResult(
            message=PREVIEW_MESSAGE,
            generated_content=content,
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
    content = (
        "Based on system records only, a pending health note draft was created from confirmed user input. "
        f"draft_id={draft_id}; status={status}; formal_health_fact_created=false. "
        "Please review the draft before any formal record is saved. This does not replace a doctor's judgment."
    )
    return AgentWorkflowResult(
        message=COMPLETED_MESSAGE,
        generated_content=content,
        status=AgentTraceStatus.SUCCESS,
        tool_calls_count=1,
    )
