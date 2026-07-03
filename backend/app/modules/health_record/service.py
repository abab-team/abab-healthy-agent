from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.health_data.enums import ConfidenceLevel
from app.modules.health_record import draft_parser, repository
from app.modules.health_record.enums import (
    HealthRecordDraftStatus,
    HealthRecordDraftType,
    HealthRecordSource,
    SymptomRecordStatus,
)
from app.modules.health_record.exceptions import (
    HealthRecordDraftNotFoundError,
    HealthRecordDraftNotPendingError,
    HealthRecordDraftTypeUnsupportedError,
    InvalidHealthRecordDraftError,
    SymptomRecordNotFoundError,
)
from app.modules.health_record.models import HealthRecordDraft, SymptomRecord
from app.modules.health_record.schemas import SymptomSummary


def create_symptom_record(
    db: Session,
    *,
    user_id: UUID,
    created_by_user_id: UUID,
    raw_text: str,
    family_id: UUID | None = None,
    symptom_name: str | None = None,
    body_part: str | None = None,
    severity: int | None = None,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    possible_trigger: str | None = None,
    follow_up_needed: bool = False,
    follow_up_at: datetime | None = None,
    ai_summary: str | None = None,
    source: HealthRecordSource | str = HealthRecordSource.MANUAL,
) -> SymptomRecord:
    if not raw_text or not raw_text.strip():
        raise InvalidHealthRecordDraftError("raw_text is required")
    return repository.create_symptom_record(
        db,
        user_id=user_id,
        family_id=family_id,
        created_by_user_id=created_by_user_id,
        raw_text=raw_text.strip(),
        symptom_name=symptom_name,
        body_part=body_part,
        severity=severity,
        started_at=started_at or datetime.now(timezone.utc),
        ended_at=ended_at,
        possible_trigger=possible_trigger,
        follow_up_needed=follow_up_needed,
        follow_up_at=follow_up_at,
        confidence_level=ConfidenceLevel.MEDIUM,
        ai_summary=ai_summary,
        timeline_visible=True,
        source=_coerce_enum(HealthRecordSource, source),
    )


def get_recent_symptoms(
    db: Session,
    *,
    user_id: UUID,
    days: int = 30,
) -> list[SymptomRecord]:
    return repository.list_recent_symptom_records(db, user_id, days=days)


def get_symptom_summary(
    db: Session,
    *,
    user_id: UUID,
    days: int = 30,
) -> SymptomSummary:
    records = get_recent_symptoms(db, user_id=user_id, days=days)
    active_count = sum(1 for record in records if record.status == SymptomRecordStatus.ACTIVE)
    follow_up_count = sum(1 for record in records if record.follow_up_needed)
    names = Counter(record.symptom_name for record in records if record.symptom_name)
    return SymptomSummary(
        days=days,
        count=len(records),
        active_count=active_count,
        follow_up_needed_count=follow_up_count,
        latest_record=_record_dict(records[0]) if records else None,
        common_symptoms=[
            {"symptom_name": name, "count": count}
            for name, count in names.most_common()
        ],
        records=[_record_dict(record) for record in records],
    )


def create_health_record_draft(
    db: Session,
    *,
    user_id: UUID,
    created_by_user_id: UUID,
    raw_text: str,
    family_id: UUID | None = None,
    target_display_name: str | None = None,
    draft_type: HealthRecordDraftType | str = HealthRecordDraftType.SYMPTOM,
    extracted_json: dict | None = None,
    missing_fields: list[str] | None = None,
    safety_flags: list[str] | None = None,
    confidence_level: ConfidenceLevel | str = ConfidenceLevel.MEDIUM,
) -> HealthRecordDraft:
    if not raw_text or not raw_text.strip():
        raise InvalidHealthRecordDraftError("raw_text is required")
    if extracted_json is None:
        extracted_json = {}
    if not isinstance(extracted_json, dict):
        raise InvalidHealthRecordDraftError("extracted_json must be a dict")
    return repository.create_health_record_draft(
        db,
        user_id=user_id,
        family_id=family_id,
        created_by_user_id=created_by_user_id,
        target_display_name=target_display_name,
        raw_text=raw_text.strip(),
        draft_type=_coerce_enum(HealthRecordDraftType, draft_type),
        extracted_json=extracted_json,
        missing_fields=missing_fields,
        safety_flags=safety_flags,
        confidence_level=_coerce_enum(ConfidenceLevel, confidence_level),
        status=HealthRecordDraftStatus.PENDING,
    )


def confirm_symptom_draft(
    db: Session,
    *,
    draft_id: UUID,
    confirmed_by_user_id: UUID,
) -> SymptomRecord:
    draft = repository.get_health_record_draft(db, draft_id)
    if draft is None:
        raise HealthRecordDraftNotFoundError("health record draft not found")
    if draft.status != HealthRecordDraftStatus.PENDING:
        raise HealthRecordDraftNotPendingError("only pending drafts can be confirmed")
    if draft.draft_type not in {
        HealthRecordDraftType.SYMPTOM,
        HealthRecordDraftType.MIXED_HEALTH_RECORD,
    }:
        raise HealthRecordDraftTypeUnsupportedError("draft type cannot create symptom record")
    fields = draft_parser.symptom_fields_from_draft(draft.extracted_json)
    record = repository.create_symptom_record(
        db,
        user_id=draft.user_id,
        family_id=draft.family_id,
        created_by_user_id=confirmed_by_user_id,
        raw_text=draft.raw_text,
        symptom_name=fields["symptom_name"],
        body_part=fields["body_part"],
        severity=fields["severity"],
        duration_text=fields["duration_text"],
        occurrence_time_text=fields["occurrence_time_text"],
        possible_trigger=fields["possible_trigger"],
        related_metric_types=fields["related_metric_types"],
        action_taken=fields["action_taken"],
        follow_up_needed=fields["follow_up_needed"],
        confidence_level=draft.confidence_level,
        ai_summary=fields["ai_summary"],
        source=HealthRecordSource.AI_EXTRACTED,
    )
    repository.update_draft_status(
        db,
        draft.id,
        HealthRecordDraftStatus.CONFIRMED,
        confirmed_at=datetime.now(timezone.utc),
        confirmed_record_id=record.id,
    )
    return record


def cancel_draft(db: Session, draft_id: UUID) -> HealthRecordDraft:
    draft = repository.update_draft_status(
        db,
        draft_id,
        HealthRecordDraftStatus.CANCELLED,
    )
    if draft is None:
        raise HealthRecordDraftNotFoundError("health record draft not found")
    return draft


def update_symptom_record_status(
    db: Session,
    record_id: UUID,
    status: SymptomRecordStatus | str,
) -> SymptomRecord:
    record = repository.update_symptom_record_status(
        db,
        record_id,
        _coerce_enum(SymptomRecordStatus, status),
    )
    if record is None:
        raise SymptomRecordNotFoundError("symptom record not found")
    return record


def _coerce_enum(enum_cls: type[StrEnum], value):
    if isinstance(value, enum_cls):
        return value
    return enum_cls(value)


def _record_dict(record: SymptomRecord) -> dict:
    return {
        "id": str(record.id),
        "symptom_name": record.symptom_name,
        "body_part": record.body_part,
        "follow_up_needed": record.follow_up_needed,
        "status": record.status.value,
        "started_at": record.started_at,
        "created_at": record.created_at,
    }
