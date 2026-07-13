from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.validators import (
    Department,
    HospitalOrOrg,
    JsonDict,
    OptionalTitle,
    RawText,
    RequiredAlertText,
    STRICT_MODEL_CONFIG,
    ShortText,
    StringList,
    SummaryText,
    SuggestedAction,
    TriggerReason,
    optional_text,
    required_text,
)
from app.agent.models import AgentMemory, AgentMessage, AgentSafetyCheck, AgentSession, AgentToolCall, AgentTrace
from app.agent.schemas import AgentRunResult


AgentUserMessage = Annotated[str, required_text(2000), Field(min_length=1, max_length=2000)]
AgentWorkflowType = Annotated[str, required_text(64), Field(min_length=1, max_length=64)]
AgentSource = Annotated[str | None, optional_text(100)]
DAILY_HEALTH_BRIEF_WORKFLOW = "daily_health_brief"
CHAT_WORKFLOW = "chat"
SYMPTOM_DRAFT_CREATE_WORKFLOW = "symptom_draft_create"
MEDICAL_EVENT_DRAFT_CREATE_WORKFLOW = "medical_event_draft_create"
ALERT_CREATE_WORKFLOW = "alert_create"
FREE_TEXT_RECORD_WORKFLOW = "free_text_record_workflow"
DOCTOR_VISIT_SUMMARY_WORKFLOW = "doctor_visit_summary_workflow"
DOCUMENT_EXTRACT_WORKFLOW = "document_extract_workflow"
DAILY_REPORT_WORKFLOW = "daily_report_workflow"
HEALTH_KNOWLEDGE_QA_WORKFLOW = "health_knowledge_qa_workflow"
ALLOWED_WORKFLOW_TYPES = {
    DAILY_HEALTH_BRIEF_WORKFLOW,
    CHAT_WORKFLOW,
    SYMPTOM_DRAFT_CREATE_WORKFLOW,
    MEDICAL_EVENT_DRAFT_CREATE_WORKFLOW,
    ALERT_CREATE_WORKFLOW,
    FREE_TEXT_RECORD_WORKFLOW,
    DOCTOR_VISIT_SUMMARY_WORKFLOW,
    DOCUMENT_EXTRACT_WORKFLOW,
    DAILY_REPORT_WORKFLOW,
    HEALTH_KNOWLEDGE_QA_WORKFLOW,
}
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
    session_id: UUID | None = None
    confirmation: bool = False
    workflow_payload: dict[str, Any] | None = None


class SymptomDraftWorkflowPayload(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    raw_text: RawText | None = None
    target_display_name: ShortText = None
    extracted_json: JsonDict = None
    missing_fields: StringList = None
    safety_flags: StringList = None


class MedicalEventDraftWorkflowPayload(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    draft_title: OptionalTitle = None
    title: OptionalTitle = None
    summary: SummaryText = None
    extracted_text_preview: SummaryText = None
    structured_hints: JsonDict = None
    draft_event_type: ShortText = None
    event_date: ShortText = None
    hospital_or_org: HospitalOrOrg = None
    department: Department = None
    draft_json: JsonDict = None
    source_document_id: UUID | None = None
    extraction_result_id: UUID | None = None
    missing_fields: StringList = None
    safety_flags: StringList = None


class AlertCreateWorkflowPayload(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    title: OptionalTitle = None
    message: RequiredAlertText | None = None
    description: RequiredAlertText | None = None
    alert_type: ShortText = None
    level: ShortText = None
    suggested_action: SuggestedAction = None
    trigger_reason: TriggerReason = None
    related_entity_type: ShortText = None
    related_entity_id: UUID | None = None
    due_at: ShortText = None
    remind_at: ShortText = None
    scheduled_at: ShortText = None
    source: ShortText = None


class DoctorVisitSummaryWorkflowPayload(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    days: int = Field(default=30, ge=1, le=365)
    limit: int = Field(default=10, ge=1, le=50)


class DocumentExtractWorkflowPayload(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    document_id: UUID | None = None
    file_name: OptionalTitle = None
    mime_type: ShortText = None


class DailyReportWorkflowPayload(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    days: int = Field(default=7, ge=1, le=365)


class HealthKnowledgeQAWorkflowPayload(BaseModel):
    model_config = STRICT_MODEL_CONFIG


def workflow_payload_for_runtime(payload: AgentRunCreateRequest) -> dict[str, Any] | None:
    raw_payload = payload.workflow_payload or {}
    if payload.workflow_type == DAILY_HEALTH_BRIEF_WORKFLOW:
        if raw_payload:
            raise ValueError("workflow_payload is not supported for daily_health_brief")
        return None
    if payload.workflow_type == CHAT_WORKFLOW:
        if raw_payload:
            raise ValueError("workflow_payload is not supported for chat")
        return None
    if payload.workflow_type == SYMPTOM_DRAFT_CREATE_WORKFLOW:
        return SymptomDraftWorkflowPayload.model_validate(raw_payload).model_dump(exclude_none=True)
    if payload.workflow_type == FREE_TEXT_RECORD_WORKFLOW:
        return SymptomDraftWorkflowPayload.model_validate(raw_payload).model_dump(exclude_none=True)
    if payload.workflow_type == MEDICAL_EVENT_DRAFT_CREATE_WORKFLOW:
        return MedicalEventDraftWorkflowPayload.model_validate(raw_payload).model_dump(exclude_none=True)
    if payload.workflow_type == ALERT_CREATE_WORKFLOW:
        return _alert_payload_for_runtime(AlertCreateWorkflowPayload.model_validate(raw_payload))
    if payload.workflow_type == DOCTOR_VISIT_SUMMARY_WORKFLOW:
        return DoctorVisitSummaryWorkflowPayload.model_validate(raw_payload).model_dump(exclude_none=True)
    if payload.workflow_type == DOCUMENT_EXTRACT_WORKFLOW:
        return DocumentExtractWorkflowPayload.model_validate(raw_payload).model_dump(exclude_none=True)
    if payload.workflow_type == DAILY_REPORT_WORKFLOW:
        return DailyReportWorkflowPayload.model_validate(raw_payload).model_dump(exclude_none=True)
    if payload.workflow_type == HEALTH_KNOWLEDGE_QA_WORKFLOW:
        return HealthKnowledgeQAWorkflowPayload.model_validate(raw_payload).model_dump(exclude_none=True)
    raise ValueError("workflow_type is not available")


class AgentRunResponse(BaseModel):
    trace_id: UUID | None
    status: str
    workflow_type: str
    message: str
    blocked: bool
    safety_level: str
    tool_calls_count: int
    generated_content: str | None = None
    session_id: str | None = None
    suggested_action: str | None = None
    conversation_task: dict[str, Any] | None = None


class AgentSessionResponse(BaseModel):
    id: UUID
    family_id: UUID | None = None
    title: str | None = None
    last_active_at: datetime
    created_at: datetime


class AgentMessageResponse(BaseModel):
    id: UUID
    role: str
    content_summary: str
    intent: str | None = None
    member_label: str | None = None
    metric_type: str | None = None
    time_range_label: str | None = None
    time_range_days: int | None = None
    tool_name: str | None = None
    created_at: datetime


class AgentMemoryItemResponse(BaseModel):
    id: UUID
    family_id: UUID | None = None
    memory_type: str
    content: str
    confidence: int
    source: str
    is_user_editable: bool
    created_at: datetime
    updated_at: datetime


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
        session_id=result.session_id,
        suggested_action=_safe_text(result.suggested_action, max_length=64),
        conversation_task=_safe_mapping(result.conversation_task),
    )


def agent_session_response(session: AgentSession) -> AgentSessionResponse:
    return AgentSessionResponse(
        id=session.id,
        family_id=session.family_id,
        title=_safe_text(session.title, max_length=120),
        last_active_at=session.last_active_at,
        created_at=session.created_at,
    )


def agent_message_response(message: AgentMessage) -> AgentMessageResponse:
    return AgentMessageResponse(
        id=message.id,
        role=_safe_text(message.role, max_length=32) or "unknown",
        content_summary=_safe_text(message.content_summary, max_length=500) or "",
        intent=_safe_text(message.intent, max_length=100),
        member_label=_safe_text(message.member_label, max_length=64),
        metric_type=_safe_text(message.metric_type, max_length=64),
        time_range_label=_safe_text(message.time_range_label, max_length=64),
        time_range_days=message.time_range_days,
        tool_name=_safe_text(message.tool_name, max_length=100),
        created_at=message.created_at,
    )


def agent_memory_item_response(item: AgentMemory) -> AgentMemoryItemResponse:
    return AgentMemoryItemResponse(
        id=item.id,
        family_id=item.family_id,
        memory_type=_safe_text(item.memory_type.value, max_length=64) or "unknown",
        content=_safe_text(item.content, max_length=500) or "",
        confidence=_confidence_score(item.confidence_level.value),
        source=_safe_text(item.source.value, max_length=64) or "system",
        is_user_editable=item.status.value == "active",
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def agent_trace_response(trace: AgentTrace) -> AgentTraceResponse:
    return AgentTraceResponse(
        trace_id=trace.id,
        request_id=trace.request_id,
        workflow_type=_workflow_type_for_response(trace.workflow_name.value, trace.raw_input_summary),
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


def agent_safety_check_response(check: AgentSafetyCheck, *, workflow_type: str | None = None) -> AgentSafetyCheckResponse:
    return AgentSafetyCheckResponse(
        id=check.id,
        workflow_type=workflow_type or check.workflow_name.value,
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


def _confidence_score(level: str) -> int:
    if level == "high":
        return 90
    if level == "medium":
        return 70
    if level == "low":
        return 40
    return 50


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


def _workflow_type_for_response(stored_workflow_type: str, raw_input_summary: str | None) -> str:
    if raw_input_summary is None:
        return stored_workflow_type
    prefix = "workflow="
    if not raw_input_summary.startswith(prefix):
        return stored_workflow_type
    requested = raw_input_summary[len(prefix) :].split(";", 1)[0].strip()
    if requested in ALLOWED_WORKFLOW_TYPES:
        return requested
    return stored_workflow_type


def _alert_payload_for_runtime(payload: AlertCreateWorkflowPayload) -> dict[str, Any]:
    message = payload.message or payload.description
    if not payload.title:
        raise ValueError("title is required for alert_create")
    if not message:
        raise ValueError("message or description is required for alert_create")
    alert_type = payload.alert_type
    level = payload.level
    if alert_type and alert_type.lower() == "emergency":
        raise ValueError("emergency alerting is not available through alert_create")
    if level and level.lower() == "urgent":
        raise ValueError("urgent emergency alerting is not available through alert_create")
    due_at = payload.due_at or payload.remind_at or payload.scheduled_at
    result: dict[str, Any] = {
        "title": payload.title,
        "message": message,
    }
    optional_values = {
        "alert_type": alert_type,
        "level": level,
        "suggested_action": payload.suggested_action,
        "trigger_reason": payload.trigger_reason,
        "related_entity_type": payload.related_entity_type,
        "related_entity_id": str(payload.related_entity_id) if payload.related_entity_id else None,
        "due_at": due_at,
    }
    result.update({key: value for key, value in optional_values.items() if value is not None})
    return result
