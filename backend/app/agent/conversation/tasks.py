from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.models import AgentConversationTask
from app.db.mixins import utc_now


ACTIVE_TASK_STATUSES = ("collecting", "ready_for_preview", "awaiting_confirmation", "pending_confirmation")
PAUSED_TASK_STATUS = "paused"
DEFAULT_TASK_TTL_MINUTES = 30
SENSITIVE_TASK_KEYS = {"raw_text", "raw_extracted_text", "file_path", "token", "password", "api_key", "private_key"}


def get_active_task(db: Session, *, session_id: UUID | str | None) -> AgentConversationTask | None:
    parsed_session_id = _parse_uuid(session_id)
    if parsed_session_id is None:
        return None
    task = db.scalar(
        select(AgentConversationTask)
        .where(
            AgentConversationTask.session_id == parsed_session_id,
            AgentConversationTask.status.in_(ACTIVE_TASK_STATUSES),
        )
        .order_by(AgentConversationTask.updated_at.desc())
    )
    if task is not None and task.expires_at is not None and _is_expired(task.expires_at):
        task.status = "expired"
        db.flush()
        return None
    return task


def get_latest_paused_task(db: Session, *, session_id: UUID | str | None) -> AgentConversationTask | None:
    """Return a resumable draft task without making it active again."""
    parsed_session_id = _parse_uuid(session_id)
    if parsed_session_id is None:
        return None
    task = db.scalar(
        select(AgentConversationTask)
        .where(
            AgentConversationTask.session_id == parsed_session_id,
            AgentConversationTask.status == PAUSED_TASK_STATUS,
        )
        .order_by(AgentConversationTask.updated_at.desc())
    )
    if task is not None and task.expires_at is not None and _is_expired(task.expires_at):
        task.status = "expired"
        db.flush()
        return None
    return task


def create_task(
    db: Session,
    *,
    session_id: UUID | str,
    task_type: str,
    task_payload: dict[str, Any] | None = None,
    missing_fields: list[str] | None = None,
    target_member: str | None = None,
    ttl_minutes: int = DEFAULT_TASK_TTL_MINUTES,
) -> AgentConversationTask | None:
    parsed_session_id = _parse_uuid(session_id)
    if parsed_session_id is None:
        return None
    active = get_active_task(db, session_id=parsed_session_id)
    if active is not None:
        active.status = "cancelled"
    task = AgentConversationTask(
        session_id=parsed_session_id,
        task_type=task_type[:64],
        status="collecting",
        task_payload=_safe_task_payload(task_payload),
        missing_fields=_safe_missing_fields(missing_fields),
        target_member=(target_member or "")[:64] or None,
        expires_at=utc_now() + timedelta(minutes=max(1, min(ttl_minutes, 120))),
    )
    db.add(task)
    db.flush()
    return task


def update_task(
    db: Session,
    task: AgentConversationTask,
    *,
    task_payload: dict[str, Any] | None = None,
    missing_fields: list[str] | None = None,
    status: str | None = None,
) -> AgentConversationTask:
    if task_payload is not None:
        task.task_payload = _safe_task_payload(task_payload)
    if missing_fields is not None:
        task.missing_fields = _safe_missing_fields(missing_fields)
    if status is not None:
        task.status = status[:32]
    task.expires_at = utc_now() + timedelta(minutes=DEFAULT_TASK_TTL_MINUTES)
    db.flush()
    return task


def cancel_task(db: Session, task: AgentConversationTask) -> AgentConversationTask:
    task.status = "cancelled"
    db.flush()
    return task


def pause_task(db: Session, task: AgentConversationTask) -> AgentConversationTask:
    """Keep a draft available while another conversational intent is handled."""
    task.status = PAUSED_TASK_STATUS
    db.flush()
    return task


def resume_task(db: Session, task: AgentConversationTask) -> AgentConversationTask:
    task.status = "collecting" if task.missing_fields else "ready_for_preview"
    task.expires_at = utc_now() + timedelta(minutes=DEFAULT_TASK_TTL_MINUTES)
    db.flush()
    return task


def safe_task_summary(task: AgentConversationTask | None) -> dict[str, Any] | None:
    if task is None:
        return None
    return {
        "id": str(task.id),
        "task_type": task.task_type,
        "status": task.status,
        "missing_fields": list(task.missing_fields or [])[:5],
        "target_member": task.target_member,
        "expires_at": task.expires_at.isoformat() if task.expires_at else None,
        "draft": _safe_card_payload(task.task_payload),
    }


def create_pending_confirmation_task(
    db: Session,
    *,
    session_id: UUID | str,
    candidate: dict[str, Any],
) -> AgentConversationTask | None:
    """Persist a user-confirmable candidate, never a health fact."""
    task = create_task(
        db,
        session_id=session_id,
        task_type="quick_note_draft",
        task_payload=candidate,
        missing_fields=[],
    )
    if task is not None:
        update_task(db, task, status="pending_confirmation")
    return task


def _safe_card_payload(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return None
    allowed = {"candidate_type", "summary", "occurred_at_hint", "duration_hint", "details", "raw_description", "destination", "metric_type", "value", "unit", "measured_at", "systolic", "diastolic", "pulse", "title", "message"}
    return {key: value for key, value in payload.items() if key in allowed and isinstance(value, (str, int, float, bool, type(None)))} or None


def _safe_task_payload(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return None
    safe: dict[str, Any] = {}
    for key, value in payload.items():
        normalized_key = str(key).lower().replace("-", "_")
        if normalized_key in SENSITIVE_TASK_KEYS or normalized_key.endswith("_token") or normalized_key.endswith("_key"):
            continue
        if isinstance(value, str):
            safe[str(key)] = value[:120]
        elif isinstance(value, (int, float, bool)) or value is None:
            safe[str(key)] = value
    return safe or None


def _safe_missing_fields(value: list[str] | None) -> list[str] | None:
    if not value:
        return None
    return [str(item)[:64] for item in value[:8]]


def _parse_uuid(value: UUID | str | None) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if value is None:
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _is_expired(expires_at) -> bool:  # noqa: ANN001
    """Compare SQLite's naive datetimes and timezone-aware production values safely."""
    now = utc_now()
    if getattr(expires_at, "tzinfo", None) is None:
        now = now.replace(tzinfo=None)
    return expires_at <= now
