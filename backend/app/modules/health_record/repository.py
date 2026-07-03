from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.health_data.enums import ConfidenceLevel
from app.modules.health_record.enums import (
    HealthRecordDraftStatus,
    HealthRecordDraftType,
    HealthRecordSource,
    SymptomRecordStatus,
)
from app.modules.health_record.models import HealthRecordDraft, SymptomRecord


def create_symptom_record(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID | None = None,
    created_by_user_id: UUID,
    raw_text: str,
    symptom_name: str | None = None,
    body_part: str | None = None,
    severity: int | None = None,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    duration_text: str | None = None,
    occurrence_time_text: str | None = None,
    possible_trigger: str | None = None,
    related_metric_types: list[str] | None = None,
    action_taken: str | None = None,
    follow_up_needed: bool = False,
    follow_up_at: datetime | None = None,
    status: SymptomRecordStatus = SymptomRecordStatus.ACTIVE,
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM,
    ai_summary: str | None = None,
    timeline_visible: bool = True,
    source: HealthRecordSource = HealthRecordSource.MANUAL,
) -> SymptomRecord:
    record = SymptomRecord(
        user_id=user_id,
        family_id=family_id,
        created_by_user_id=created_by_user_id,
        raw_text=raw_text,
        symptom_name=symptom_name,
        body_part=body_part,
        severity=severity,
        started_at=started_at,
        ended_at=ended_at,
        duration_text=duration_text,
        occurrence_time_text=occurrence_time_text,
        possible_trigger=possible_trigger,
        related_metric_types=related_metric_types,
        action_taken=action_taken,
        follow_up_needed=follow_up_needed,
        follow_up_at=follow_up_at,
        status=status,
        confidence_level=confidence_level,
        ai_summary=ai_summary,
        timeline_visible=timeline_visible,
        source=source,
    )
    db.add(record)
    db.flush()
    return record


def get_symptom_record(db: Session, record_id: UUID) -> SymptomRecord | None:
    return db.get(SymptomRecord, record_id)


def list_symptom_records(
    db: Session,
    user_id: UUID,
    *,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    status: SymptomRecordStatus | None = None,
    limit: int = 100,
) -> list[SymptomRecord]:
    stmt = select(SymptomRecord).where(SymptomRecord.user_id == user_id)
    if start_at is not None:
        stmt = stmt.where(SymptomRecord.started_at >= start_at)
    if end_at is not None:
        stmt = stmt.where(SymptomRecord.started_at <= end_at)
    if status is not None:
        stmt = stmt.where(SymptomRecord.status == status)
    return list(db.scalars(stmt.order_by(SymptomRecord.created_at.desc()).limit(limit)))


def list_recent_symptom_records(
    db: Session,
    user_id: UUID,
    *,
    days: int = 30,
    limit: int = 50,
) -> list[SymptomRecord]:
    start_at = datetime.now(timezone.utc) - timedelta(days=days)
    return list_symptom_records(db, user_id, start_at=start_at, limit=limit)


def list_follow_up_symptoms(
    db: Session,
    user_id: UUID,
    *,
    due_before: datetime | None = None,
) -> list[SymptomRecord]:
    stmt = select(SymptomRecord).where(
        SymptomRecord.user_id == user_id,
        SymptomRecord.follow_up_needed.is_(True),
    )
    if due_before is not None:
        stmt = stmt.where(SymptomRecord.follow_up_at <= due_before)
    return list(db.scalars(stmt.order_by(SymptomRecord.follow_up_at.asc())))


def update_symptom_record_status(
    db: Session,
    record_id: UUID,
    status: SymptomRecordStatus,
) -> SymptomRecord | None:
    record = get_symptom_record(db, record_id)
    if record is None:
        return None
    record.status = status
    db.flush()
    return record


def create_health_record_draft(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID | None = None,
    created_by_user_id: UUID,
    target_display_name: str | None = None,
    raw_text: str,
    draft_type: HealthRecordDraftType,
    extracted_json: dict,
    missing_fields: list[str] | None = None,
    safety_flags: list[str] | None = None,
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM,
    status: HealthRecordDraftStatus = HealthRecordDraftStatus.PENDING,
    expires_at: datetime | None = None,
) -> HealthRecordDraft:
    draft = HealthRecordDraft(
        user_id=user_id,
        family_id=family_id,
        created_by_user_id=created_by_user_id,
        target_display_name=target_display_name,
        raw_text=raw_text,
        draft_type=draft_type,
        extracted_json=extracted_json,
        missing_fields=missing_fields,
        safety_flags=safety_flags,
        confidence_level=confidence_level,
        status=status,
        expires_at=expires_at,
    )
    db.add(draft)
    db.flush()
    return draft


def get_health_record_draft(
    db: Session,
    draft_id: UUID,
) -> HealthRecordDraft | None:
    return db.get(HealthRecordDraft, draft_id)


def list_pending_drafts(
    db: Session,
    user_id: UUID,
    *,
    family_id: UUID | None = None,
    limit: int = 50,
) -> list[HealthRecordDraft]:
    stmt = select(HealthRecordDraft).where(
        HealthRecordDraft.user_id == user_id,
        HealthRecordDraft.status == HealthRecordDraftStatus.PENDING,
    )
    if family_id is not None:
        stmt = stmt.where(HealthRecordDraft.family_id == family_id)
    return list(db.scalars(stmt.order_by(HealthRecordDraft.created_at.desc()).limit(limit)))


def update_draft_status(
    db: Session,
    draft_id: UUID,
    status: HealthRecordDraftStatus,
    *,
    confirmed_at: datetime | None = None,
    confirmed_record_id: UUID | None = None,
) -> HealthRecordDraft | None:
    draft = get_health_record_draft(db, draft_id)
    if draft is None:
        return None
    draft.status = status
    if confirmed_at is not None:
        draft.confirmed_at = confirmed_at
    if confirmed_record_id is not None:
        draft.confirmed_record_id = confirmed_record_id
    db.flush()
    return draft
