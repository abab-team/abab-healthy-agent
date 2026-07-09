from __future__ import annotations

from app.agent.enums import AgentWorkflowName
from app.agent.langgraph.graphs.draft_tool_graph import DraftToolGraph
from app.agent.schemas import AgentWorkflowContext, ToolExecutionRequest, ToolExecutionResult


class MedicalEventDraftGraph(DraftToolGraph):
    def __init__(self, *, executor) -> None:
        from app.agent.workflows import medical_event_draft_create as workflow

        def execute(context: AgentWorkflowContext) -> ToolExecutionResult:
            return executor.execute(
                context.db,
                ToolExecutionRequest(
                    trace_id=context.trace_id,
                    tool_name=workflow.TOOL_NAME,
                    actor_user_id=context.request.actor_user_id,
                    target_user_id=context.request.target_user_id,
                    family_id=context.request.family_id,
                    input_data=workflow._tool_input(context),
                    confirmed=context.request.confirmation,
                    safety_level=context.safety_level,
                    reason=workflow.WORKFLOW_TYPE,
                ),
            )

        super().__init__(
            workflow_name=AgentWorkflowName.MEDICAL_EVENT_DRAFT_CREATE_WORKFLOW,
            graph_name="medical_event_draft_graph",
            execute_tool=execute,
            build_result=workflow._workflow_result,
        )
