from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.health_data.enums import ConfidenceLevel
from app.modules.medical_timeline.enums import (
    MedicalEventSource,
    MedicalEventStatus,
    MedicalEventType,
)
from app.modules.medical_timeline.models import MedicalEvent


def create_medical_event(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID | None = None,
    created_by_user_id: UUID,
    event_type: MedicalEventType,
    title: str,
    event_date: date | None = None,
    event_date_text: str | None = None,
    hospital_or_org: str | None = None,
    department: str | None = None,
    diagnosis_text: str | None = None,
    summary: str | None = None,
    doctor_advice: str | None = None,
    medications: list[dict] | None = None,
    key_findings: list[dict] | None = None,
    follow_up_needed: bool = False,
    follow_up_at: datetime | None = None,
    related_document_id: UUID | None = None,
    source: MedicalEventSource = MedicalEventSource.MANUAL,
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM,
    timeline_visible: bool = True,
    status: MedicalEventStatus = MedicalEventStatus.ACTIVE,
) -> MedicalEvent:
    event = MedicalEvent(
        user_id=user_id,
        family_id=family_id,
        created_by_user_id=created_by_user_id,
        event_type=event_type,
        title=title,
        event_date=event_date,
        event_date_text=event_date_text,
        hospital_or_org=hospital_or_org,
        department=department,
        diagnosis_text=diagnosis_text,
        summary=summary,
        doctor_advice=doctor_advice,
        medications=medications,
        key_findings=key_findings,
        follow_up_needed=follow_up_needed,
        follow_up_at=follow_up_at,
        related_document_id=related_document_id,
        source=source,
        confidence_level=confidence_level,
        timeline_visible=timeline_visible,
        status=status,
    )
    db.add(event)
    db.flush()
    return event


def get_medical_event(db: Session, event_id: UUID) -> MedicalEvent | None:
    return db.get(MedicalEvent, event_id)


def list_medical_events(
    db: Session,
    user_id: UUID,
    *,
    event_type: MedicalEventType | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    status: MedicalEventStatus | None = None,
    limit: int = 100,
) -> list[MedicalEvent]:
    stmt = select(MedicalEvent).where(MedicalEvent.user_id == user_id)
    if event_type is not None:
        stmt = stmt.where(MedicalEvent.event_type == event_type)
    if start_date is not None:
        stmt = stmt.where(MedicalEvent.event_date >= start_date)
    if end_date is not None:
        stmt = stmt.where(MedicalEvent.event_date <= end_date)
    if status is not None:
        stmt = stmt.where(MedicalEvent.status == status)
    stmt = stmt.order_by(MedicalEvent.event_date.desc().nullslast(), MedicalEvent.created_at.desc())
    return list(db.scalars(stmt.limit(limit)))


def list_recent_medical_events(
    db: Session,
    user_id: UUID,
    *,
    days: int = 365,
    limit: int = 50,
) -> list[MedicalEvent]:
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).date()
    return list_medical_events(db, user_id, start_date=start_date, limit=limit)


def list_follow_up_events(
    db: Session,
    user_id: UUID,
    *,
    due_before: datetime | None = None,
) -> list[MedicalEvent]:
    stmt = select(MedicalEvent).where(
        MedicalEvent.user_id == user_id,
        MedicalEvent.follow_up_needed.is_(True),
        MedicalEvent.status == MedicalEventStatus.ACTIVE,
    )
    if due_before is not None:
        stmt = stmt.where(MedicalEvent.follow_up_at <= due_before)
    return list(db.scalars(stmt.order_by(MedicalEvent.follow_up_at.asc().nullslast())))


def update_medical_event(
    db: Session,
    event_id: UUID,
    **fields,
) -> MedicalEvent | None:
    event = get_medical_event(db, event_id)
    if event is None:
        return None
    for key, value in fields.items():
        setattr(event, key, value)
    db.flush()
    return event


def archive_medical_event(db: Session, event_id: UUID) -> MedicalEvent | None:
    return update_medical_event(db, event_id, status=MedicalEventStatus.ARCHIVED)
