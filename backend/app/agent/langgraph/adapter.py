from __future__ import annotations

from collections.abc import Callable

from app.agent import service as agent_service
from app.agent.enums import AgentSafetyLevel, AgentWorkflowName
from app.agent.langgraph.state import HealthAgentGraphState, validate_no_sensitive_state
from app.agent.schemas import AgentWorkflowContext


CHAT_HEALTH_QUERY_NODES = (
    "input_safety",
    "parse_intent",
    "permission_gate",
    "tool_execution",
    "compose_answer",
    "output_safety",
)


class LangGraphExecutionAdapter:
    """Optional graph orchestration adapter.

    The adapter is deliberately thin in Phase 17. It does not call tools, read
    database tables, write business data, or bypass AgentRuntime safety. It only
    wraps an existing deterministic workflow runner and records a safe graph node
    summary when graph orchestration is enabled.
    """

    def __init__(self, settings) -> None:
        self.settings = settings

    def chat_query_enabled(self) -> bool:
        return bool(self.settings.LANGGRAPH_ENABLED and self.settings.LANGGRAPH_CHAT_QUERY_ENABLED)

    def daily_brief_enabled(self) -> bool:
        return bool(self.settings.LANGGRAPH_ENABLED and self.settings.LANGGRAPH_DAILY_BRIEF_ENABLED)

    def run_chat_health_query(self, context: AgentWorkflowContext, runner: Callable[[], object]):
        if not self.chat_query_enabled():
            return runner()

        trace = agent_service.get_trace(context.db, context.trace_id)
        request_id = trace.request_id if trace is not None else context.request.request_id or str(context.trace_id)
        initial_state = HealthAgentGraphState(
            trace_id=context.trace_id,
            request_id=request_id,
            workflow_type=AgentWorkflowName.CHAT_WORKFLOW.value,
            actor_user_id=context.request.actor_user_id,
            target_user_id=context.request.target_user_id,
            family_id=context.request.family_id,
            user_message_excerpt=(context.request.user_message or "")[:160],
            safety_level=str(context.safety_level),
            node_summary=("input_safety", "parse_intent"),
            metadata={"graph": "chat_health_query_graph"},
        )
        validate_no_sensitive_state(initial_state.safe_summary())

        result = runner()
        graph_nodes = list(CHAT_HEALTH_QUERY_NODES)
        object.__setattr__(result, "graph_node_summary", graph_nodes)

        if self.settings.LANGGRAPH_TRACE_NODE_SUMMARY:
            agent_service.record_safety_check(
                context.db,
                request_id=request_id,
                workflow_name=AgentWorkflowName.CHAT_WORKFLOW,
                safety_level=AgentSafetyLevel.SAFE,
                passed=True,
                intent="graph_node_summary",
                safety_flags=["langgraph", "chat_health_query_graph"],
                input_risk_summary="graph_nodes=" + " > ".join(graph_nodes),
                revised_answer_summary="safe_graph_node_summary",
            )
        return result
