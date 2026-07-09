from __future__ import annotations

from collections.abc import Callable

from app.agent import service as agent_service
from app.agent.enums import AgentSafetyLevel, AgentWorkflowName
import app.agent.langgraph.nodes as nodes
from app.agent.langgraph.state import HealthAgentGraphState, validate_no_sensitive_state
from app.agent.schemas import AgentWorkflowContext


CHAT_HEALTH_QUERY_NODES = (
    "load_memory",
    "input_safety",
    "rule_parse",
    "route_by_confidence",
    "llm_plan_skipped",
    "validate_plan",
    "permission_gate",
    "execute_tools",
    "compose_answer",
    "critic_review",
    "output_safety",
    "memory_update",
    "trace_record",
)


class LangGraphExecutionAdapter:
    """Optional graph orchestration adapter.

    The adapter carries a safe state graph for chat query orchestration. It does
    not call tools directly, read health tables, write business data, or bypass
    AgentRuntime safety. Tool execution remains delegated to the existing
    workflow, which uses ToolExecutor and permission checks.
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
        state = HealthAgentGraphState(
            trace_id=context.trace_id,
            request_id=request_id,
            workflow_type=AgentWorkflowName.CHAT_WORKFLOW.value,
            actor_user_id=context.request.actor_user_id,
            target_user_id=context.request.target_user_id,
            family_id=context.request.family_id,
            user_message_excerpt=(context.request.user_message or "")[:160],
            safety_level=str(context.safety_level),
            metadata={"graph": "chat_health_query_graph"},
        )
        validate_no_sensitive_state(state.safe_summary())

        try:
            state = nodes.load_memory_node(state)
            state = nodes.input_safety_node(state)
            state = nodes.rule_parse_node(state)
            state = nodes.route_by_confidence_node(state)
            state = nodes.llm_plan_node(state)
            state = nodes.validate_plan_node(state)
            if (state.validated_plan or {}).get("status") == "needs_clarification":
                state = nodes.ask_clarification_node(state)
            else:
                state = nodes.permission_gate_node(state)
            state, result = nodes.execute_tools_node(state, runner)
            state = nodes.compose_answer_node(state)
            state = nodes.critic_review_node(state)
            state = nodes.output_safety_node(state)
            state = nodes.memory_update_node(state)
            state = nodes.trace_record_node(state, final_answer=getattr(result, "answer", None))
        except Exception as exc:
            if self.settings.LANGGRAPH_STRICT_MODE:
                raise
            state = nodes.fallback_node(state, exc.__class__.__name__)
            result = runner()

        graph_nodes = list(state.node_summary)
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
                revised_answer_summary=f"safe_graph_state:{state.graph_status}",
            )
        return result
