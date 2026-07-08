from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


SENSITIVE_STATE_KEYS = {
    "api_key",
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
    "traceback",
}


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
    tool_names: tuple[str, ...] = ()
    node_summary: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def safe_summary(self) -> dict[str, Any]:
        validate_no_sensitive_state(self.metadata)
        return {
            "workflow_type": self.workflow_type,
            "safety_level": self.safety_level,
            "intent": self.intent,
            "tool_count": len(self.tool_names),
            "node_summary": list(self.node_summary),
        }


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
