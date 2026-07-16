"""Controlled quick-note candidate lifecycle.

Candidates live only in ``agent_conversation_tasks`` until the initiating user
explicitly confirms them. This module intentionally contains no LLM calls.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.agent.conversation import tasks
from app.modules.alerts import service as alerts_service
from app.modules.document_processing import service as document_service
from app.modules.health_data import service as health_data_service
from app.modules.health_data.enums import MetricSource
from app.modules.health_record import service as health_record_service
from app.modules.health_record.enums import HealthRecordDraftType

ALLOWED_CANDIDATE_TYPES = {"symptom", "metric", "medical_event", "alert"}


def create_pending_candidate(db: Session, *, session_id: UUID | str, candidate: dict[str, Any]) -> dict[str, Any]:
    normalized = validate_candidate(candidate)
    task = tasks.create_pending_confirmation_task(db, session_id=session_id, candidate=normalized)
    if task is None:
        raise ValueError("a conversation session is required")
    return tasks.safe_task_summary(task) or {}


def validate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    candidate_type = str(candidate.get("candidate_type") or "").strip()
    if candidate_type not in ALLOWED_CANDIDATE_TYPES:
        raise ValueError("unsupported quick-note candidate")
    summary = _text(candidate.get("summary"), 120)
    details = _text(candidate.get("details") or candidate.get("raw_description"), 500)
    if not summary and not details:
        raise ValueError("candidate content is required")
    result: dict[str, Any] = {
        "candidate_type": candidate_type,
        "summary": summary or details,
        "details": details or summary,
        "raw_description": _text(candidate.get("raw_description"), 500) or details or summary,
        "occurred_at_hint": _text(candidate.get("occurred_at_hint"), 80),
        "duration_hint": _text(candidate.get("duration_hint"), 80),
    }
    if candidate_type == "symptom":
        result["destination"] = "档案 > 健康记录 > 症状记录"
    elif candidate_type == "metric":
        metric_type = _text(candidate.get("metric_type"), 64)
        value = candidate.get("value")
        if not metric_type or not isinstance(value, (int, float)):
            raise ValueError("metric candidate requires metric_type and numeric value")
        result.update({"metric_type": metric_type, "value": float(value), "unit": _text(candidate.get("unit"), 24), "destination": "档案 > 健康指标"})
        result.update({
            "measured_at": _text(candidate.get("measured_at"), 64),
            "systolic": candidate.get("systolic"),
            "diastolic": candidate.get("diastolic"),
            "pulse": candidate.get("pulse"),
        })
    elif candidate_type == "medical_event":
        result.update({"title": _text(candidate.get("title"), 120) or summary, "destination": "档案 > 就医历史"})
    else:
        result.update({"title": _text(candidate.get("title"), 120) or summary, "message": _text(candidate.get("message"), 300) or details, "destination": "提醒 > 普通健康提醒"})
    return result


def get_owned_pending_task(db: Session, *, task_id: UUID, session_id: UUID, user_id: UUID):
    task = db.get(tasks.AgentConversationTask, task_id)
    if task is None or task.session_id != session_id or task.status != "pending_confirmation":
        return None
    # Session ownership is checked by the API before this function is called.
    return task


def cancel_pending_task(db: Session, task) -> dict[str, Any]:
    tasks.cancel_task(db, task)
    return tasks.safe_task_summary(task) or {}


def update_pending_task(db: Session, task, updates: dict[str, Any]) -> dict[str, Any]:
    payload = dict(task.task_payload or {})
    for key in ("summary", "details", "occurred_at_hint", "duration_hint", "title", "message"):
        if key in updates:
            payload[key] = updates[key]
    tasks.update_task(db, task, task_payload=validate_candidate(payload), status="pending_confirmation")
    return tasks.safe_task_summary(task) or {}


def confirm_pending_task(db: Session, *, task, user_id: UUID, family_id: UUID | None = None) -> dict[str, Any]:
    """Map a confirmed candidate to an existing explicit health model."""
    payload = dict(task.task_payload or {})
    candidate_type = payload["candidate_type"]
    if candidate_type == "symptom":
        draft = health_record_service.create_health_record_draft(
            db, user_id=user_id, family_id=family_id, created_by_user_id=user_id,
            raw_text=payload["raw_description"], draft_type=HealthRecordDraftType.SYMPTOM,
            extracted_json={"symptom": payload["summary"], "occurred_at_hint": payload.get("occurred_at_hint"), "duration_hint": payload.get("duration_hint"), "details": payload["details"]},
        )
        health_record_service.confirm_symptom_draft(db, draft_id=draft.id, confirmed_by_user_id=user_id)
    elif candidate_type == "metric":
        measured_at = _parse_measured_at(payload.get("measured_at"))
        if payload.get("metric_type") in {"blood_pressure", "blood-pressure"}:
            diastolic = _optional_int(payload.get("diastolic"))
            if diastolic is None:
                raise ValueError("blood pressure candidate requires diastolic value")
            health_data_service.add_blood_pressure_record(
                db, user_id=user_id, systolic=int(payload.get("systolic") or payload["value"]),
                diastolic=diastolic, pulse=_optional_int(payload.get("pulse")), measured_at=measured_at,
                note=payload.get("details"), source=MetricSource.AI_EXTRACTED,
            )
        else:
            health_data_service.add_metric(
                db, user_id=user_id, metric_type=payload["metric_type"], value_numeric=payload["value"],
                unit=payload.get("unit") or None, measured_at=measured_at, note=payload.get("details"),
                source=MetricSource.AI_EXTRACTED,
            )
    elif candidate_type == "medical_event":
        draft = document_service.create_medical_event_draft(db, user_id=user_id, family_id=family_id, created_by_user_id=user_id, draft_title=payload["title"], draft_event_type="other", draft_json={"summary": payload["details"]})
        document_service.confirm_medical_event_draft(db, draft_id=draft.id, confirmed_by_user_id=user_id)
    else:
        alerts_service.create_alert(db, user_id=user_id, family_id=family_id, created_by_user_id=user_id, title=payload["title"], message=payload["message"], alert_type="health", level="normal")
    tasks.update_task(db, task, status="confirmed")
    return tasks.safe_task_summary(task) or {}


def confirm_pending_task_by_id(db: Session, *, task_id: UUID, session_id: UUID, user_id: UUID, family_id: UUID | None = None) -> dict[str, Any]:
    task = get_owned_pending_task(db, task_id=task_id, session_id=session_id, user_id=user_id)
    if task is None:
        raise ValueError("pending quick-note task is not available")
    return confirm_pending_task(db, task=task, user_id=user_id, family_id=family_id)


def _text(value: Any, max_length: int) -> str:
    return str(value or "").strip()[:max_length]


def _parse_measured_at(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _optional_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
