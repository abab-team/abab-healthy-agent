from __future__ import annotations

from typing import Any

from app.agent.enums import AgentTraceStatus, AgentWorkflowName
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult, ToolExecutionRequest, ToolExecutionResult
from app.agent.tool_executor import AgentToolExecutor
from app.agent.tool_registry import AgentToolRegistry
from app.agent.tools.health_record_tools import SymptomDraftCreateTool


WORKFLOW_TYPE = "symptom_draft_create"
TOOL_NAME = "health_record.symptom_draft.create"
CONFIRMATION_REQUIRED_MESSAGE = "requires_confirmation=true; no draft was created."
BLOCKED_MESSAGE = "Draft workflow was blocked safely. No target data was returned."
COMPLETED_MESSAGE = "Pending symptom draft created from confirmed user input."


class SymptomDraftCreateWorkflow:
    workflow_name = AgentWorkflowName.FREE_TEXT_RECORD_WORKFLOW

    def __init__(self, executor: AgentToolExecutor | None = None) -> None:
        if executor is None:
            registry = AgentToolRegistry()
            registry.register(SymptomDraftCreateTool())
            executor = AgentToolExecutor(registry)
        self.executor = executor

    def run(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
        tool_result = self.executor.execute(
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
        return _workflow_result(tool_result)


def _tool_input(context: AgentWorkflowContext) -> dict[str, Any]:
    payload = dict(context.request.workflow_payload or {})
    payload.setdefault("raw_text", context.request.user_message)
    return payload


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
    content = f"{COMPLETED_MESSAGE} draft_id={draft_id}; status={status}; formal_record_created=false."
    return AgentWorkflowResult(
        message=COMPLETED_MESSAGE,
        generated_content=content,
        status=AgentTraceStatus.SUCCESS,
        tool_calls_count=1,
    )
