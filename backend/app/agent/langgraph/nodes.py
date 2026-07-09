from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.agent.chat import parse_health_query
from app.agent.langgraph.state import HealthAgentGraphState, append_node


def load_memory_node(state: HealthAgentGraphState) -> HealthAgentGraphState:
    return append_node(state, "load_memory", memory_context_summary=("session_context_loaded_by_workflow",))


def input_safety_node(state: HealthAgentGraphState) -> HealthAgentGraphState:
    return append_node(state, "input_safety")


def rule_parse_node(state: HealthAgentGraphState) -> HealthAgentGraphState:
    plan = parse_health_query(state.user_message_excerpt)
    summary = {
        "intent": plan.intent.value,
        "member_scope": plan.member_scope,
        "time_range": plan.time_range.label,
        "needs_clarification": plan.needs_clarification,
        "planner_source": plan.planner_source,
        "has_tool_mapping": bool(plan.tool_name),
    }
    return append_node(state, "rule_parse", intent=plan.intent.value, rule_plan=summary)


def route_by_confidence_node(state: HealthAgentGraphState) -> HealthAgentGraphState:
    route = "rule_low_confidence"
    if state.rule_plan and state.rule_plan.get("has_tool_mapping"):
        route = "rule_high_confidence"
    return append_node(state, "route_by_confidence", metadata={**state.metadata, "confidence_route": route})


def llm_plan_node(state: HealthAgentGraphState) -> HealthAgentGraphState:
    if state.metadata.get("confidence_route") == "rule_high_confidence":
        return append_node(state, "llm_plan_skipped", llm_plan={"status": "skipped_rule_high_confidence"})
    return append_node(state, "llm_plan", llm_plan={"status": "delegated_to_workflow_if_enabled"})


def validate_plan_node(state: HealthAgentGraphState) -> HealthAgentGraphState:
    plan = state.rule_plan or {}
    status = "valid" if plan.get("has_tool_mapping") else "needs_clarification"
    if plan.get("needs_clarification"):
        status = "needs_clarification"
    return append_node(state, "validate_plan", validated_plan={"status": status, "intent": plan.get("intent")})


def ask_clarification_node(state: HealthAgentGraphState) -> HealthAgentGraphState:
    return append_node(state, "ask_clarification")


def permission_gate_node(state: HealthAgentGraphState) -> HealthAgentGraphState:
    return append_node(state, "permission_gate", permission_status="delegated_to_tool_executor")


def execute_tools_node(state: HealthAgentGraphState, runner: Callable[[], Any]) -> tuple[HealthAgentGraphState, Any]:
    result = runner()
    summary = (
        {
            "status": "completed",
            "count": getattr(result, "tool_calls_count", 0),
            "executor": "ToolExecutor",
        },
    )
    next_state = append_node(
        state,
        "execute_tools",
        tool_results_summary=summary,
        draft_answer=_safe_excerpt(getattr(result, "answer", "")),
    )
    return next_state, result


def compose_answer_node(state: HealthAgentGraphState) -> HealthAgentGraphState:
    return append_node(state, "compose_answer")


def critic_review_node(state: HealthAgentGraphState) -> HealthAgentGraphState:
    return append_node(state, "critic_review", critic_result={"status": "delegated_to_workflow_critic"})


def safe_rewrite_node(state: HealthAgentGraphState) -> HealthAgentGraphState:
    return append_node(state, "safe_rewrite")


def output_safety_node(state: HealthAgentGraphState) -> HealthAgentGraphState:
    return append_node(state, "output_safety")


def memory_update_node(state: HealthAgentGraphState) -> HealthAgentGraphState:
    return append_node(state, "memory_update", metadata={**state.metadata, "memory_update": "delegated_to_workflow"})


def trace_record_node(state: HealthAgentGraphState, final_answer: str | None = None) -> HealthAgentGraphState:
    return append_node(state, "trace_record", final_answer=_safe_excerpt(final_answer), graph_status="completed")


def fallback_node(state: HealthAgentGraphState, reason: str) -> HealthAgentGraphState:
    return append_node(
        state,
        "fallback",
        graph_status="fallback",
        errors=tuple(list(state.errors) + [_safe_excerpt(reason, 120)]),
    )


def _safe_excerpt(value: str | None, max_length: int = 240) -> str | None:
    text = str(value or "").strip()
    return text[:max_length] if text else None
