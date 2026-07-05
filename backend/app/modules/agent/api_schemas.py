from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.validators import STRICT_MODEL_CONFIG, optional_text, required_text
from app.agent.models import AgentSafetyCheck, AgentToolCall, AgentTrace
from app.agent.schemas import AgentRunResult


AgentUserMessage = Annotated[str, required_text(2000), Field(min_length=1, max_length=2000)]
AgentWorkflowType = Annotated[str, required_text(64), Field(min_length=1, max_length=64)]
AgentSource = Annotated[str | None, optional_text(100)]
ALLOWED_WORKFLOW_TYPE = "daily_health_brief"
SENSITIVE_KEYS = {
    "access_token",
    "api_key",
    "file_path",
    "key",
    "password",
    "password_hash",
    "private_key",
    "raw_text",
    "raw_extracted_text",
    "refresh_token",
    "secret",
    "session_token",
    "symptom_text",
    "token",
}


class AgentRunCreateRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    target_user_id: UUID
    family_id: UUID | None = None
    workflow_type: AgentWorkflowType
    user_message: AgentUserMessage
    source: AgentSource = None


class AgentRunResponse(BaseModel):
    trace_id: UUID | None
    status: str
    workflow_type: str
    message: str
    blocked: bool
    safety_level: str
    tool_calls_count: int
    generated_content: str | None = None


class AgentTraceResponse(BaseModel):
    trace_id: UUID
    request_id: str
    workflow_type: str
    status: str
    target_user_id: UUID | None = None
    family_id: UUID | None = None
    source: str | None = None
    input_summary: str | None = None
    output_summary: str | None = None
    error_type: str | None = None
    started_at: datetime
    ended_at: datetime | None = None
    duration_ms: int | None = None


class AgentToolCallResponse(BaseModel):
    id: UUID
    tool_name: str
    access_mode: str
    risk_level: str
    target_user_id: UUID | None = None
    permission_checked: bool
    permission_result: dict[str, Any] | None = None
    input_summary: dict[str, Any] | None = None
    output_summary: dict[str, Any] | None = None
    status: str
    error_type: str | None = None
    duration_ms: int | None = None
    created_at: datetime


class AgentSafetyCheckResponse(BaseModel):
    id: UUID
    workflow_type: str
    intent: str | None = None
    safety_level: str
    safety_flags: list[str] | None = None
    passed: bool
    was_rewritten: bool
    blocked_reason: str | None = None
    input_risk_summary: str | None = None
    original_answer_summary: str | None = None
    revised_answer_summary: str | None = None
    created_at: datetime


def agent_run_response(result: AgentRunResult) -> AgentRunResponse:
    return AgentRunResponse(
        trace_id=result.trace_id,
        status=result.status,
        workflow_type=result.workflow_type,
        message=_safe_text(result.message, max_length=500),
        blocked=result.blocked,
        safety_level=result.safety_level,
        tool_calls_count=result.tool_calls_count,
        generated_content=_safe_text(result.generated_content, max_length=6000),
    )


def agent_trace_response(trace: AgentTrace) -> AgentTraceResponse:
    return AgentTraceResponse(
        trace_id=trace.id,
        request_id=trace.request_id,
        workflow_type=trace.workflow_name.value,
        status=trace.status.value,
        target_user_id=trace.target_user_id,
        family_id=trace.current_family_id,
        source=_safe_text(trace.source_page, max_length=100),
        input_summary=_safe_text(trace.raw_input_summary, max_length=300),
        output_summary=_safe_text(trace.final_output_summary, max_length=1000),
        error_type=trace.error_type,
        started_at=trace.started_at,
        ended_at=trace.ended_at,
        duration_ms=trace.duration_ms,
    )


def agent_tool_call_response(tool_call: AgentToolCall) -> AgentToolCallResponse:
    return AgentToolCallResponse(
        id=tool_call.id,
        tool_name=tool_call.tool_name,
        access_mode=tool_call.access_mode.value,
        risk_level=tool_call.risk_level.value,
        target_user_id=tool_call.target_user_id,
        permission_checked=tool_call.permission_checked,
        permission_result=_safe_mapping(tool_call.permission_result),
        input_summary=_safe_mapping(tool_call.input_summary),
        output_summary=_safe_mapping(tool_call.output_summary),
        status=tool_call.status.value,
        error_type=tool_call.error_type,
        duration_ms=tool_call.duration_ms,
        created_at=tool_call.created_at,
    )


def agent_safety_check_response(check: AgentSafetyCheck) -> AgentSafetyCheckResponse:
    return AgentSafetyCheckResponse(
        id=check.id,
        workflow_type=check.workflow_name.value,
        intent=_safe_text(check.intent, max_length=100),
        safety_level=check.safety_level.value,
        safety_flags=check.safety_flags,
        passed=check.passed,
        was_rewritten=check.was_rewritten,
        blocked_reason=_safe_text(check.blocked_reason, max_length=100),
        input_risk_summary=_safe_text(check.input_risk_summary, max_length=200),
        original_answer_summary=_safe_text(check.original_answer_summary, max_length=200),
        revised_answer_summary=_safe_text(check.revised_answer_summary, max_length=200),
        created_at=check.created_at,
    )


def _safe_mapping(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    summary: dict[str, Any] = {}
    redacted_count = 0
    for key, item in value.items():
        key_text = str(key)
        if _is_sensitive_key(key_text):
            redacted_count += 1
            summary[f"redacted_field_{redacted_count}"] = {"type": "redacted"}
            continue
        summary[key_text] = _safe_value(item)
    return summary


def _safe_value(value: Any) -> Any:
    if isinstance(value, str):
        return _safe_text(value, max_length=200)
    if isinstance(value, dict):
        return _safe_mapping(value)
    if isinstance(value, list):
        return [_safe_value(item) for item in value[:20]]
    return value


def _safe_text(value: str | None, *, max_length: int) -> str | None:
    if value is None:
        return None
    text = str(value)
    if _contains_sensitive_marker(text):
        return "[redacted]"
    return text[:max_length]


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return normalized in SENSITIVE_KEYS or normalized.endswith("_token") or normalized.endswith("_key")


def _contains_sensitive_marker(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in SENSITIVE_KEYS)
