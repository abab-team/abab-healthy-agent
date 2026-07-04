from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.enums import AgentSafetyLevel, AgentTraceStatus, AgentTriggerType, AgentWorkflowName
from app.agent.models import AgentSafetyCheck, AgentTrace


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
