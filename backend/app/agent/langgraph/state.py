from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict
from uuid import UUID


SENSITIVE_STATE_KEYS = {
    "api_key",
    "current_user_id",
    "family_id_from_llm",
    "file_path",
    "input_data",
    "password",
    "private_key",
    "raw_extracted_text",
    "raw_llm_response",
    "raw_prompt",
    "raw_text",
    "sql",
    "symptom_text",
    "token",
    "tool_name",
    "target_user_id_from_llm",
    "traceback",
}


class BaseAgentGraphState(TypedDict, total=False):
    trace_id: UUID
    request_id: str
    workflow_name: str
    actor_user_id: UUID
    target_user_id: UUID | None
    family_id: UUID | None
    user_message_excerpt: str
    safety_level: str
    node_summary: list[str]
    graph_status: str
    errors: list[str]
    permission_status: str | None
    critic_flags: list[str]
    final_answer: str | None
    generated_content: str | None
    tool_calls_count: int
    metadata: dict[str, Any]


@dataclass(frozen=True)
class HealthAgentGraphState:
    trace_id: UUID
    request_id: str
    workflow_type: str
    actor_user_id: UUID
    target_user_id: UUID | None
    family_id: UUID | None
    user_message_excerpt: str
    safety_level: str
    intent: str | None = None
    memory_context_summary: tuple[str, ...] = ()
    rule_plan: dict[str, Any] | None = None
    llm_plan: dict[str, Any] | None = None
    validated_plan: dict[str, Any] | None = None
    permission_status: str | None = None
    tool_results_summary: tuple[dict[str, Any], ...] = ()
    draft_answer: str | None = None
    critic_result: dict[str, Any] | None = None
    final_answer: str | None = None
    graph_status: str = "running"
    node_summary: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def safe_summary(self) -> dict[str, Any]:
        validate_no_sensitive_state(self.metadata)
        validate_no_sensitive_state(self.rule_plan or {})
        validate_no_sensitive_state(self.llm_plan or {})
        validate_no_sensitive_state(self.validated_plan or {})
        validate_no_sensitive_state(list(self.tool_results_summary))
        validate_no_sensitive_state(self.critic_result or {})
        return {
            "workflow_type": self.workflow_type,
            "safety_level": self.safety_level,
            "intent": self.intent,
            "tool_count": len(self.tool_results_summary),
            "permission_status": self.permission_status,
            "graph_status": self.graph_status,
            "node_summary": list(self.node_summary),
            "errors": list(self.errors),
        }


def append_node(state: HealthAgentGraphState, node_name: str, **updates: Any) -> HealthAgentGraphState:
    values = dict(state.__dict__)
    values.update(updates)
    values["node_summary"] = tuple(list(state.node_summary) + [node_name])
    next_state = HealthAgentGraphState(**values)
    validate_no_sensitive_state(next_state.safe_summary())
    return next_state


def initial_graph_state(
    *,
    trace_id: UUID,
    request_id: str,
    workflow_name: str,
    actor_user_id: UUID,
    target_user_id: UUID | None,
    family_id: UUID | None,
    user_message: str,
    safety_level: str,
    graph_name: str,
) -> BaseAgentGraphState:
    state: BaseAgentGraphState = {
        "trace_id": trace_id,
        "request_id": request_id,
        "workflow_name": workflow_name,
        "actor_user_id": actor_user_id,
        "target_user_id": target_user_id,
        "family_id": family_id,
        "user_message_excerpt": str(user_message or "")[:160],
        "safety_level": safety_level,
        "node_summary": [],
        "graph_status": "running",
        "errors": [],
        "permission_status": None,
        "critic_flags": [],
        "final_answer": None,
        "generated_content": None,
        "tool_calls_count": 0,
        "metadata": {"graph": graph_name},
    }
    validate_no_sensitive_state(graph_safe_summary(state))
    return state


def append_graph_node(state: BaseAgentGraphState, node_name: str, **updates: Any) -> BaseAgentGraphState:
    next_state: BaseAgentGraphState = dict(state)
    next_state.update(updates)
    next_state["node_summary"] = [*state.get("node_summary", []), node_name]
    validate_no_sensitive_state(graph_safe_summary(next_state))
    return next_state


def graph_safe_summary(state: BaseAgentGraphState) -> dict[str, Any]:
    summary = {
        "workflow_name": state.get("workflow_name"),
        "safety_level": state.get("safety_level"),
        "graph_status": state.get("graph_status"),
        "permission_status": state.get("permission_status"),
        "tool_calls_count": state.get("tool_calls_count", 0),
        "node_summary": list(state.get("node_summary", [])),
        "critic_flags": list(state.get("critic_flags", [])),
        "errors": list(state.get("errors", [])),
        "metadata": dict(state.get("metadata", {})),
    }
    validate_no_sensitive_state(summary)
    return summary


def validate_no_sensitive_state(value: Any, *, path: str = "state") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower()
            if any(sensitive in normalized for sensitive in SENSITIVE_STATE_KEYS):
                raise ValueError(f"sensitive graph state key is not allowed: {path}.{key}")
            validate_no_sensitive_state(item, path=f"{path}.{key}")
        return
    if isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            validate_no_sensitive_state(item, path=f"{path}[{index}]")
