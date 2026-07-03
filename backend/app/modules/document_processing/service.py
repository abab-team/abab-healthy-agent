from __future__ import annotations

from datetime import date, datetime, timezone
from enum import StrEnum
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.document_center import repository as document_repository
from app.modules.document_center.enums import DocumentExtractStatus
from app.modules.document_processing import repository
from app.modules.document_processing.enums import (
    DocumentExtractionMode,
    DocumentExtractionResultStatus,
    DocumentProcessingJobType,
    DocumentProcessingStatus,
    MedicalEventDraftStatus,
)
from app.modules.document_processing.exceptions import (
    DocumentProcessingJobNotFoundError,
    InvalidMedicalEventDraftError,
    MedicalEventDraftNotFoundError,
    MedicalEventDraftNotPendingError,
)
from app.modules.document_processing.models import (
    DocumentExtractionResult,
    DocumentProcessingJob,
    MedicalEventDraft,
)
from app.modules.health_data.enums import ConfidenceLevel
from app.modules.medical_timeline import service as medical_event_service
from app.modules.medical_timeline.enums import MedicalEventSource, MedicalEventType
from app.modules.medical_timeline.models import MedicalEvent


def create_processing_job(
    db: Session,
    *,
    document_id: UUID,
    user_id: UUID,
    family_id: UUID | None = None,
    job_type: DocumentProcessingJobType | str = DocumentProcessingJobType.AI_EXTRACT,
) -> DocumentProcessingJob:
    return repository.create_processing_job(
        db,
        document_id=document_id,
        user_id=user_id,
        family_id=family_id,
        job_type=_coerce_enum(DocumentProcessingJobType, job_type),
    )


def mark_job_started(db: Session, job_id: UUID) -> DocumentProcessingJob:
    job = repository.update_processing_job_status(
        db,
        job_id,
        DocumentProcessingStatus.PROCESSING,
        started_at=datetime.now(timezone.utc),
        increment_attempt=True,
    )
    if job is None:
        raise DocumentProcessingJobNotFoundError("document processing job not found")
    return job


def mark_job_success(db: Session, job_id: UUID) -> DocumentProcessingJob:
    job = repository.update_processing_job_status(
        db,
        job_id,
        DocumentProcessingStatus.SUCCESS,
        finished_at=datetime.now(timezone.utc),
    )
    if job is None:
        raise DocumentProcessingJobNotFoundError("document processing job not found")
    return job


def mark_job_failed(
    db: Session,
    job_id: UUID,
    error_message: str,
) -> DocumentProcessingJob:
    job = repository.update_processing_job_status(
        db,
        job_id,
        DocumentProcessingStatus.FAILED,
        error_message=error_message,
        finished_at=datetime.now(timezone.utc),
    )
    if job is None:
        raise DocumentProcessingJobNotFoundError("document processing job not found")
    return job


def save_extraction_result(
    db: Session,
    *,
    document_id: UUID,
    user_id: UUID,
    processing_job_id: UUID | None = None,
    family_id: UUID | None = None,
    extraction_mode: DocumentExtractionMode | str = DocumentExtractionMode.STANDARD,
    ai_summary: str | None = None,
    key_findings: list[dict] | None = None,
    doctor_advice: str | None = None,
    suggested_events: list[dict] | None = None,
    raw_extracted_text: str | None = None,
    confidence_level: ConfidenceLevel | str = ConfidenceLevel.MEDIUM,
    safety_notes: list[str] | None = None,
    status: DocumentExtractionResultStatus | str = DocumentExtractionResultStatus.DRAFT,
) -> DocumentExtractionResult:
    return repository.create_extraction_result(
        db,
        document_id=document_id,
        processing_job_id=processing_job_id,
        user_id=user_id,
        family_id=family_id,
        extraction_mode=_coerce_enum(DocumentExtractionMode, extraction_mode),
        ai_summary=ai_summary,
        key_findings=key_findings,
        doctor_advice=doctor_advice,
        suggested_events=suggested_events,
        raw_extracted_text=raw_extracted_text,
        confidence_level=_coerce_enum(ConfidenceLevel, confidence_level),
        safety_notes=safety_notes,
        status=_coerce_enum(DocumentExtractionResultStatus, status),
    )


def create_medical_event_draft(
    db: Session,
    *,
    user_id: UUID,
    created_by_user_id: UUID,
    draft_event_type: MedicalEventType | str,
    draft_json: dict,
    family_id: UUID | None = None,
    source_document_id: UUID | None = None,
    extraction_result_id: UUID | None = None,
    draft_title: str | None = None,
    missing_fields: list[str] | None = None,
    confidence_level: ConfidenceLevel | str = ConfidenceLevel.MEDIUM,
    safety_flags: list[str] | None = None,
    expires_at: datetime | None = None,
) -> MedicalEventDraft:
    if not isinstance(draft_json, dict):
        raise InvalidMedicalEventDraftError("draft_json must be a dict")
    return repository.create_medical_event_draft(
        db,
        user_id=user_id,
        family_id=family_id,
        created_by_user_id=created_by_user_id,
        source_document_id=source_document_id,
        extraction_result_id=extraction_result_id,
        draft_event_type=_coerce_enum(MedicalEventType, draft_event_type),
        draft_title=draft_title,
        draft_json=draft_json,
        missing_fields=missing_fields,
        confidence_level=_coerce_enum(ConfidenceLevel, confidence_level),
        safety_flags=safety_flags,
        expires_at=expires_at,
    )


def list_pending_medical_event_drafts(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID | None = None,
) -> list[MedicalEventDraft]:
    return repository.list_pending_medical_event_drafts(db, user_id, family_id=family_id)


def confirm_medical_event_draft(
    db: Session,
    *,
    draft_id: UUID,
    confirmed_by_user_id: UUID,
) -> MedicalEvent:
    draft = repository.get_medical_event_draft(db, draft_id)
    if draft is None:
        raise MedicalEventDraftNotFoundError("medical event draft not found")
    if draft.status != MedicalEventDraftStatus.PENDING:
        raise MedicalEventDraftNotPendingError("only pending drafts can be confirmed")

    payload = _medical_event_payload(draft.draft_json)
    title = payload.get("title") or draft.draft_title
    summary = payload.get("summary")
    if not title and not summary:
        raise InvalidMedicalEventDraftError("draft must include title or summary")
    if not title:
        title = str(summary)[:120]

    event = medical_event_service.create_medical_event(
        db,
        user_id=draft.user_id,
        family_id=draft.family_id,
        created_by_user_id=confirmed_by_user_id,
        event_type=payload.get("event_type") or draft.draft_event_type,
        title=title,
        event_date=_parse_date(payload.get("event_date")),
        event_date_text=payload.get("event_date_text"),
        hospital_or_org=payload.get("hospital_or_org"),
        department=payload.get("department"),
        diagnosis_text=payload.get("diagnosis_text"),
        summary=summary,
        doctor_advice=payload.get("doctor_advice"),
        medications=payload.get("medications"),
        key_findings=payload.get("key_findings"),
        follow_up_needed=bool(payload.get("follow_up_needed", False)),
        follow_up_at=_parse_datetime(payload.get("follow_up_at")),
        related_document_id=draft.source_document_id,
        source=payload.get("source") or MedicalEventSource.DOCUMENT_EXTRACTED,
        confidence_level=draft.confidence_level,
    )
    repository.update_medical_event_draft_status(
        db,
        draft.id,
        MedicalEventDraftStatus.CONFIRMED,
        confirmed_event_id=event.id,
        confirmed_at=datetime.now(timezone.utc),
    )
    if draft.source_document_id is not None:
        document_repository.increment_related_event_count(
            db,
            draft.source_document_id,
            count=1,
        )
        document_repository.update_extract_status(
            db,
            draft.source_document_id,
            DocumentExtractStatus.CONFIRMED,
            confirmed_at=datetime.now(timezone.utc),
        )
    return event


def cancel_medical_event_draft(db: Session, draft_id: UUID) -> MedicalEventDraft:
    draft = repository.update_medical_event_draft_status(
        db,
        draft_id,
        MedicalEventDraftStatus.CANCELLED,
    )
    if draft is None:
        raise MedicalEventDraftNotFoundError("medical event draft not found")
    return draft


def _medical_event_payload(draft_json: dict) -> dict:
    if not isinstance(draft_json, dict):
        raise InvalidMedicalEventDraftError("draft_json must be a dict")
    event_payload = draft_json.get("medical_event", draft_json)
    if not isinstance(event_payload, dict):
        raise InvalidMedicalEventDraftError("medical_event must be a dict")
    return event_payload


def _parse_date(value) -> date | None:
    if value is None or isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        return date.fromisoformat(value)
    return None


def _parse_datetime(value) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        return datetime.fromisoformat(value)
    return None


def _coerce_enum(enum_cls: type[StrEnum], value):
    if isinstance(value, enum_cls):
        return value
    return enum_cls(value)
