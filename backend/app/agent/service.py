from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.agent import repository
from app.agent.enums import (
    AgentSafetyLevel,
    AgentToolAccessMode,
    AgentToolCallStatus,
    AgentToolRiskLevel,
    AgentTraceStatus,
    AgentTriggerType,
    AgentWorkflowName,
)
from app.agent.exceptions import AgentRuntimeError
from app.agent.models import AgentSafetyCheck, AgentToolCall, AgentTrace
from app.db.mixins import utc_now


def start_trace(
    db: Session,
    *,
    request_id: str,
    workflow_name: AgentWorkflowName,
    current_user_id: UUID,
    target_user_id: UUID | None,
    current_family_id: UUID | None = None,
    session_id: str | None = None,
    source_page: str | None = None,
    raw_input_summary: str | None = None,
    trigger_type: AgentTriggerType = AgentTriggerType.USER_CHAT,
) -> AgentTrace:
    return repository.create_trace(
        db,
        request_id=request_id,
        workflow_name=workflow_name,
        current_user_id=current_user_id,
        current_family_id=current_family_id,
        target_user_id=target_user_id,
        session_id=session_id,
        source_page=source_page,
        raw_input_summary=raw_input_summary,
        trigger_type=trigger_type,
        started_at=utc_now(),
    )


def get_trace_by_request_id(db: Session, request_id: str) -> AgentTrace | None:
    return repository.get_trace_by_request_id(db, request_id)


def complete_trace(db: Session, trace_id: UUID, *, final_output_summary: str | None = None) -> AgentTrace:
    trace = _require_trace(db, trace_id)
    completed = repository.mark_trace_completed(
        db,
        trace_id,
        ended_at=utc_now(),
        duration_ms=_duration_ms(trace.started_at, utc_now()),
        final_output_summary=final_output_summary,
    )
    if completed is None:
        raise AgentRuntimeError("trace not found")
    return completed


def fail_trace(
    db: Session,
    trace_id: UUID,
    *,
    error_type: str,
    error_message: str,
    final_output_summary: str | None = None,
    status: AgentTraceStatus = AgentTraceStatus.FAILED,
) -> AgentTrace:
    trace = _require_trace(db, trace_id)
    failed = repository.mark_trace_failed(
        db,
        trace_id,
        ended_at=utc_now(),
        duration_ms=_duration_ms(trace.started_at, utc_now()),
        error_type=error_type[:100],
        error_message=error_message[:1000],
        final_output_summary=final_output_summary,
        status=status,
    )
    if failed is None:
        raise AgentRuntimeError("trace not found")
    return failed


def record_safety_check(
    db: Session,
    *,
    request_id: str,
    workflow_name: AgentWorkflowName,
    safety_level: AgentSafetyLevel,
    passed: bool,
    intent: str | None = None,
    safety_flags: list[str] | None = None,
    blocked_reason: str | None = None,
    input_risk_summary: str | None = None,
    original_answer_summary: str | None = None,
    revised_answer_summary: str | None = None,
    was_rewritten: bool = False,
) -> AgentSafetyCheck:
    return repository.create_safety_check(
        db,
        request_id=request_id,
        workflow_name=workflow_name,
        safety_level=safety_level,
        passed=passed,
        intent=intent,
        safety_flags=safety_flags,
        blocked_reason=blocked_reason,
        input_risk_summary=input_risk_summary,
        original_answer_summary=original_answer_summary,
        revised_answer_summary=revised_answer_summary,
        was_rewritten=was_rewritten,
    )


def get_trace(db: Session, trace_id: UUID) -> AgentTrace | None:
    return repository.get_trace(db, trace_id)


def list_safety_checks(db: Session, *, request_id: str | None = None, workflow_name: AgentWorkflowName | None = None) -> list[AgentSafetyCheck]:
    return repository.list_safety_checks(db, request_id=request_id, workflow_name=workflow_name)


def start_tool_call(
    db: Session,
    *,
    trace_id: UUID,
    tool_name: str,
    access_mode: AgentToolAccessMode,
    risk_level: AgentToolRiskLevel,
    current_user_id: UUID,
    target_user_id: UUID | None,
    input_summary: dict | None = None,
    permission_checked: bool = False,
    permission_result: dict | None = None,
    status: AgentToolCallStatus = AgentToolCallStatus.SKIPPED,
) -> AgentToolCall:
    trace = _require_trace(db, trace_id)
    return repository.create_tool_call(
        db,
        request_id=trace.request_id,
        workflow_name=trace.workflow_name,
        tool_name=tool_name[:100],
        access_mode=access_mode,
        risk_level=risk_level,
        current_user_id=current_user_id,
        target_user_id=target_user_id,
        input_summary=input_summary,
        permission_checked=permission_checked,
        permission_result=permission_result,
        status=status,
    )


def complete_tool_call(
    db: Session,
    tool_call_id: UUID,
    *,
    output_summary: dict | None = None,
) -> AgentToolCall:
    tool_call = _require_tool_call(db, tool_call_id)
    completed = repository.mark_tool_call_completed(
        db,
        tool_call_id,
        output_summary=output_summary,
        duration_ms=_duration_ms(tool_call.created_at, utc_now()),
    )
    if completed is None:
        raise AgentRuntimeError("tool call not found")
    return completed


def fail_tool_call(
    db: Session,
    tool_call_id: UUID,
    *,
    error_type: str,
    error_message: str,
    output_summary: dict | None = None,
) -> AgentToolCall:
    tool_call = _require_tool_call(db, tool_call_id)
    failed = repository.mark_tool_call_failed(
        db,
        tool_call_id,
        error_type=error_type[:100],
        error_message=error_message[:1000],
        output_summary=output_summary,
        duration_ms=_duration_ms(tool_call.created_at, utc_now()),
    )
    if failed is None:
        raise AgentRuntimeError("tool call not found")
    return failed


def block_tool_call(
    db: Session,
    tool_call_id: UUID,
    *,
    status: AgentToolCallStatus,
    error_type: str,
    error_message: str,
    permission_checked: bool | None = None,
    permission_result: dict | None = None,
    output_summary: dict | None = None,
) -> AgentToolCall:
    tool_call = _require_tool_call(db, tool_call_id)
    blocked = repository.mark_tool_call_blocked(
        db,
        tool_call_id,
        status=status,
        error_type=error_type[:100],
        error_message=error_message[:1000],
        permission_checked=permission_checked,
        permission_result=permission_result,
        output_summary=output_summary,
        duration_ms=_duration_ms(tool_call.created_at, utc_now()),
    )
    if blocked is None:
        raise AgentRuntimeError("tool call not found")
    return blocked


def list_tool_calls(db: Session, *, trace_id: UUID) -> list[AgentToolCall]:
    return repository.list_tool_calls_by_trace(db, trace_id)


def _require_trace(db: Session, trace_id: UUID) -> AgentTrace:
    trace = repository.get_trace(db, trace_id)
    if trace is None:
        raise AgentRuntimeError("trace not found")
    return trace


def _require_tool_call(db: Session, tool_call_id: UUID) -> AgentToolCall:
    tool_call = repository.get_tool_call(db, tool_call_id)
    if tool_call is None:
        raise AgentRuntimeError("tool call not found")
    return tool_call


def _duration_ms(started_at: datetime, ended_at: datetime) -> int:
    return max(0, int((ended_at - started_at).total_seconds() * 1000))
