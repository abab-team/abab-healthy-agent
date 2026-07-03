from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.health_data.enums import ConfidenceLevel
from app.modules.medical_timeline import repository
from app.modules.medical_timeline.enums import (
    MedicalEventSource,
    MedicalEventStatus,
    MedicalEventType,
)
from app.modules.medical_timeline.exceptions import (
    InvalidMedicalEventError,
    MedicalEventNotFoundError,
)
from app.modules.medical_timeline.models import MedicalEvent
from app.modules.medical_timeline.schemas import MedicalEventSummary


def create_medical_event(
    db: Session,
    *,
    user_id: UUID,
    created_by_user_id: UUID,
    event_type: MedicalEventType | str,
    title: str,
    family_id: UUID | None = None,
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
    source: MedicalEventSource | str = MedicalEventSource.MANUAL,
    confidence_level: ConfidenceLevel | str = ConfidenceLevel.MEDIUM,
    timeline_visible: bool = True,
    status: MedicalEventStatus | str = MedicalEventStatus.ACTIVE,
) -> MedicalEvent:
    if not title or not title.strip():
        raise InvalidMedicalEventError("title is required")
    if created_by_user_id is None:
        raise InvalidMedicalEventError("created_by_user_id is required")
    return repository.create_medical_event(
        db,
        user_id=user_id,
        family_id=family_id,
        created_by_user_id=created_by_user_id,
        event_type=_coerce_enum(MedicalEventType, event_type),
        title=title.strip(),
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
        source=_coerce_enum(MedicalEventSource, source),
        confidence_level=_coerce_enum(ConfidenceLevel, confidence_level),
        timeline_visible=timeline_visible,
        status=_coerce_enum(MedicalEventStatus, status),
    )


def get_medical_event(db: Session, event_id: UUID) -> MedicalEvent:
    event = repository.get_medical_event(db, event_id)
    if event is None:
        raise MedicalEventNotFoundError("medical event not found")
    return event


def get_medical_timeline(
    db: Session,
    *,
    user_id: UUID,
    days: int = 365,
    event_type: MedicalEventType | str | None = None,
) -> list[MedicalEvent]:
    coerced_type = _coerce_enum(MedicalEventType, event_type) if event_type is not None else None
    if coerced_type is None:
        return repository.list_recent_medical_events(db, user_id, days=days)
    return repository.list_medical_events(
        db,
        user_id,
        event_type=coerced_type,
        limit=100,
    )


def get_recent_medical_events(
    db: Session,
    *,
    user_id: UUID,
    days: int = 365,
) -> list[MedicalEvent]:
    return repository.list_recent_medical_events(db, user_id, days=days)


def get_follow_up_events(
    db: Session,
    *,
    user_id: UUID,
    due_before: datetime | None = None,
) -> list[MedicalEvent]:
    return repository.list_follow_up_events(db, user_id, due_before=due_before)


def archive_medical_event(db: Session, event_id: UUID) -> MedicalEvent:
    event = repository.archive_medical_event(db, event_id)
    if event is None:
        raise MedicalEventNotFoundError("medical event not found")
    return event


def get_medical_event_summary(
    db: Session,
    *,
    user_id: UUID,
    days: int = 365,
) -> MedicalEventSummary:
    events = get_recent_medical_events(db, user_id=user_id, days=days)
    follow_up_count = sum(1 for event in events if event.follow_up_needed)
    return MedicalEventSummary(
        days=days,
        count=len(events),
        follow_up_needed_count=follow_up_count,
        latest_event=_event_dict(events[0]) if events else None,
        events=[_event_dict(event) for event in events],
    )


def _coerce_enum(enum_cls: type[StrEnum], value):
    if isinstance(value, enum_cls):
        return value
    return enum_cls(value)


def _event_dict(event: MedicalEvent) -> dict:
    return {
        "id": str(event.id),
        "event_type": event.event_type.value,
        "title": event.title,
        "event_date": event.event_date,
        "follow_up_needed": event.follow_up_needed,
        "follow_up_at": event.follow_up_at,
        "status": event.status.value,
    }
