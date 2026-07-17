from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.enums import (
    AgentSafetyLevel,
    AgentToolAccessMode,
    AgentToolCallStatus,
    AgentToolRiskLevel,
    AgentTraceStatus,
    AgentTriggerType,
    AgentWorkflowName,
)
from app.agent.models import AgentSafetyCheck, AgentToolCall, AgentTrace


def create_trace(
    db: Session,
    *,
    request_id: str,
    workflow_name: AgentWorkflowName,
    current_user_id: UUID,
    trigger_type: AgentTriggerType,
    started_at: datetime,
    current_family_id: UUID | None = None,
    target_user_id: UUID | None = None,
    session_id: str | None = None,
    source_page: str | None = None,
    raw_input_summary: str | None = None,
) -> AgentTrace:
    trace = AgentTrace(
        request_id=request_id,
        session_id=session_id,
        workflow_name=workflow_name,
        trigger_type=trigger_type,
        current_user_id=current_user_id,
        current_family_id=current_family_id,
        target_user_id=target_user_id,
        source_page=source_page,
        raw_input_summary=raw_input_summary,
        status=AgentTraceStatus.RUNNING,
        started_at=started_at,
    )
    db.add(trace)
    db.flush()
    return trace


def get_trace(db: Session, trace_id: UUID) -> AgentTrace | None:
    return db.get(AgentTrace, trace_id)


def get_trace_by_request_id(db: Session, request_id: str) -> AgentTrace | None:
    stmt = select(AgentTrace).where(AgentTrace.request_id == request_id)
    return db.scalar(stmt)


def get_latest_home_daily_health_brief(db: Session, *, user_id: UUID) -> AgentTrace | None:
    stmt = (
        select(AgentTrace)
        .where(
            AgentTrace.current_user_id == user_id,
            AgentTrace.target_user_id == user_id,
            AgentTrace.workflow_name == AgentWorkflowName.DAILY_HEALTH_BRIEF,
            AgentTrace.source_page == "mobile_home_daily_health_brief",
            AgentTrace.status == AgentTraceStatus.SUCCESS,
            AgentTrace.final_output_summary.is_not(None),
        )
        .order_by(AgentTrace.ended_at.desc(), AgentTrace.created_at.desc())
    )
    return db.scalar(stmt)


def mark_trace_running(db: Session, trace_id: UUID, *, started_at: datetime | None = None) -> AgentTrace | None:
    trace = get_trace(db, trace_id)
    if trace is None:
        return None
    trace.status = AgentTraceStatus.RUNNING
    if started_at is not None:
        trace.started_at = started_at
    trace.ended_at = None
    trace.duration_ms = None
    trace.error_type = None
    trace.error_message = None
    db.flush()
    return trace


def mark_trace_completed(
    db: Session,
    trace_id: UUID,
    *,
    ended_at: datetime,
    duration_ms: int,
    final_output_summary: str | None = None,
) -> AgentTrace | None:
    trace = get_trace(db, trace_id)
    if trace is None:
        return None
    trace.status = AgentTraceStatus.SUCCESS
    trace.ended_at = ended_at
    trace.duration_ms = duration_ms
    trace.final_output_summary = final_output_summary
    trace.error_type = None
    trace.error_message = None
    db.flush()
    return trace


def mark_trace_failed(
    db: Session,
    trace_id: UUID,
    *,
    ended_at: datetime,
    duration_ms: int,
    error_type: str,
    error_message: str,
    final_output_summary: str | None = None,
    status: AgentTraceStatus = AgentTraceStatus.FAILED,
) -> AgentTrace | None:
    trace = get_trace(db, trace_id)
    if trace is None:
        return None
    trace.status = status
    trace.ended_at = ended_at
    trace.duration_ms = duration_ms
    trace.error_type = error_type
    trace.error_message = error_message
    trace.final_output_summary = final_output_summary
    db.flush()
    return trace


def create_safety_check(
    db: Session,
    *,
    request_id: str,
    workflow_name: AgentWorkflowName,
    safety_level: AgentSafetyLevel,
    passed: bool,
    intent: str | None = None,
    safety_flags: list[str] | None = None,
    was_rewritten: bool = False,
    blocked_reason: str | None = None,
    input_risk_summary: str | None = None,
    original_answer_summary: str | None = None,
    revised_answer_summary: str | None = None,
) -> AgentSafetyCheck:
    check = AgentSafetyCheck(
        request_id=request_id,
        workflow_name=workflow_name,
        intent=intent,
        safety_level=safety_level,
        safety_flags=safety_flags,
        passed=passed,
        was_rewritten=was_rewritten,
        blocked_reason=blocked_reason,
        input_risk_summary=input_risk_summary,
        original_answer_summary=original_answer_summary,
        revised_answer_summary=revised_answer_summary,
    )
    db.add(check)
    db.flush()
    return check


def list_safety_checks(db: Session, *, request_id: str | None = None, workflow_name: AgentWorkflowName | None = None) -> list[AgentSafetyCheck]:
    stmt = select(AgentSafetyCheck)
    if request_id is not None:
        stmt = stmt.where(AgentSafetyCheck.request_id == request_id)
    if workflow_name is not None:
        stmt = stmt.where(AgentSafetyCheck.workflow_name == workflow_name)
    return list(db.scalars(stmt.order_by(AgentSafetyCheck.created_at.asc())))


def create_tool_call(
    db: Session,
    *,
    request_id: str,
    workflow_name: AgentWorkflowName,
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
    tool_call = AgentToolCall(
        request_id=request_id,
        workflow_name=workflow_name,
        tool_name=tool_name,
        access_mode=access_mode,
        risk_level=risk_level,
        current_user_id=current_user_id,
        target_user_id=target_user_id,
        permission_checked=permission_checked,
        permission_result=permission_result,
        input_summary=input_summary,
        status=status,
    )
    db.add(tool_call)
    db.flush()
    return tool_call


def get_tool_call(db: Session, tool_call_id: UUID) -> AgentToolCall | None:
    return db.get(AgentToolCall, tool_call_id)


def mark_tool_call_completed(
    db: Session,
    tool_call_id: UUID,
    *,
    output_summary: dict | None = None,
    duration_ms: int | None = None,
) -> AgentToolCall | None:
    return _mark_tool_call(
        db,
        tool_call_id,
        status=AgentToolCallStatus.SUCCESS,
        output_summary=output_summary,
        duration_ms=duration_ms,
    )


def mark_tool_call_failed(
    db: Session,
    tool_call_id: UUID,
    *,
    error_type: str,
    error_message: str,
    output_summary: dict | None = None,
    duration_ms: int | None = None,
) -> AgentToolCall | None:
    return _mark_tool_call(
        db,
        tool_call_id,
        status=AgentToolCallStatus.FAILED,
        error_type=error_type,
        error_message=error_message,
        output_summary=output_summary,
        duration_ms=duration_ms,
    )


def mark_tool_call_blocked(
    db: Session,
    tool_call_id: UUID,
    *,
    status: AgentToolCallStatus,
    error_type: str,
    error_message: str,
    permission_checked: bool | None = None,
    permission_result: dict | None = None,
    output_summary: dict | None = None,
    duration_ms: int | None = None,
) -> AgentToolCall | None:
    return _mark_tool_call(
        db,
        tool_call_id,
        status=status,
        error_type=error_type,
        error_message=error_message,
        permission_checked=permission_checked,
        permission_result=permission_result,
        output_summary=output_summary,
        duration_ms=duration_ms,
    )


def list_tool_calls_by_trace(db: Session, trace_id: UUID) -> list[AgentToolCall]:
    trace = get_trace(db, trace_id)
    if trace is None:
        return []
    stmt = select(AgentToolCall).where(AgentToolCall.request_id == trace.request_id)
    return list(db.scalars(stmt.order_by(AgentToolCall.created_at.asc())))


def _mark_tool_call(
    db: Session,
    tool_call_id: UUID,
    *,
    status: AgentToolCallStatus,
    error_type: str | None = None,
    error_message: str | None = None,
    permission_checked: bool | None = None,
    permission_result: dict | None = None,
    output_summary: dict | None = None,
    duration_ms: int | None = None,
) -> AgentToolCall | None:
    tool_call = get_tool_call(db, tool_call_id)
    if tool_call is None:
        return None
    tool_call.status = status
    tool_call.error_type = error_type
    tool_call.error_message = error_message
    if permission_checked is not None:
        tool_call.permission_checked = permission_checked
    if permission_result is not None:
        tool_call.permission_result = permission_result
    if output_summary is not None:
        tool_call.output_summary = output_summary
    if duration_ms is not None:
        tool_call.duration_ms = duration_ms
    db.flush()
    return tool_call
