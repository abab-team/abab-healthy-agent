from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.document_processing.enums import (
    DocumentExtractionMode,
    DocumentExtractionResultStatus,
    DocumentProcessingJobType,
    DocumentProcessingStatus,
    MedicalEventDraftStatus,
)
from app.modules.document_processing.models import (
    DocumentExtractionResult,
    DocumentProcessingJob,
    MedicalEventDraft,
)
from app.modules.health_data.enums import ConfidenceLevel
from app.modules.medical_timeline.enums import MedicalEventType


def create_processing_job(
    db: Session,
    *,
    document_id: UUID,
    user_id: UUID,
    family_id: UUID | None = None,
    job_type: DocumentProcessingJobType,
    status: DocumentProcessingStatus = DocumentProcessingStatus.PENDING,
) -> DocumentProcessingJob:
    job = DocumentProcessingJob(
        document_id=document_id,
        user_id=user_id,
        family_id=family_id,
        job_type=job_type,
        status=status,
    )
    db.add(job)
    db.flush()
    return job


def get_processing_job(db: Session, job_id: UUID) -> DocumentProcessingJob | None:
    return db.get(DocumentProcessingJob, job_id)


def list_processing_jobs(
    db: Session,
    *,
    document_id: UUID | None = None,
    user_id: UUID | None = None,
    status: DocumentProcessingStatus | None = None,
    limit: int = 100,
) -> list[DocumentProcessingJob]:
    stmt = select(DocumentProcessingJob)
    if document_id is not None:
        stmt = stmt.where(DocumentProcessingJob.document_id == document_id)
    if user_id is not None:
        stmt = stmt.where(DocumentProcessingJob.user_id == user_id)
    if status is not None:
        stmt = stmt.where(DocumentProcessingJob.status == status)
    return list(db.scalars(stmt.order_by(DocumentProcessingJob.created_at.desc()).limit(limit)))


def update_processing_job_status(
    db: Session,
    job_id: UUID,
    status: DocumentProcessingStatus,
    *,
    error_message: str | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    increment_attempt: bool = False,
) -> DocumentProcessingJob | None:
    job = get_processing_job(db, job_id)
    if job is None:
        return None
    job.status = status
    job.error_message = error_message
    if started_at is not None:
        job.started_at = started_at
    if finished_at is not None:
        job.finished_at = finished_at
    if increment_attempt:
        job.attempt_count += 1
    db.flush()
    return job


def create_extraction_result(
    db: Session,
    *,
    document_id: UUID,
    processing_job_id: UUID | None = None,
    user_id: UUID,
    family_id: UUID | None = None,
    extraction_mode: DocumentExtractionMode = DocumentExtractionMode.STANDARD,
    ai_summary: str | None = None,
    key_findings: list[dict] | None = None,
    doctor_advice: str | None = None,
    suggested_events: list[dict] | None = None,
    raw_extracted_text: str | None = None,
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM,
    safety_notes: list[str] | None = None,
    status: DocumentExtractionResultStatus = DocumentExtractionResultStatus.DRAFT,
) -> DocumentExtractionResult:
    result = DocumentExtractionResult(
        document_id=document_id,
        processing_job_id=processing_job_id,
        user_id=user_id,
        family_id=family_id,
        extraction_mode=extraction_mode,
        ai_summary=ai_summary,
        key_findings=key_findings,
        doctor_advice=doctor_advice,
        suggested_events=suggested_events,
        raw_extracted_text=raw_extracted_text,
        confidence_level=confidence_level,
        safety_notes=safety_notes,
        status=status,
    )
    db.add(result)
    db.flush()
    return result


def get_extraction_result(
    db: Session,
    result_id: UUID,
) -> DocumentExtractionResult | None:
    return db.get(DocumentExtractionResult, result_id)


def list_extraction_results(
    db: Session,
    document_id: UUID,
    *,
    status: DocumentExtractionResultStatus | None = None,
) -> list[DocumentExtractionResult]:
    stmt = select(DocumentExtractionResult).where(DocumentExtractionResult.document_id == document_id)
    if status is not None:
        stmt = stmt.where(DocumentExtractionResult.status == status)
    return list(db.scalars(stmt.order_by(DocumentExtractionResult.created_at.desc())))


def update_extraction_result_status(
    db: Session,
    result_id: UUID,
    status: DocumentExtractionResultStatus,
) -> DocumentExtractionResult | None:
    result = get_extraction_result(db, result_id)
    if result is None:
        return None
    result.status = status
    db.flush()
    return result


def create_medical_event_draft(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID | None = None,
    created_by_user_id: UUID,
    source_document_id: UUID | None = None,
    extraction_result_id: UUID | None = None,
    draft_event_type: MedicalEventType,
    draft_title: str | None = None,
    draft_json: dict,
    missing_fields: list[str] | None = None,
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM,
    safety_flags: list[str] | None = None,
    status: MedicalEventDraftStatus = MedicalEventDraftStatus.PENDING,
    expires_at: datetime | None = None,
) -> MedicalEventDraft:
    draft = MedicalEventDraft(
        user_id=user_id,
        family_id=family_id,
        created_by_user_id=created_by_user_id,
        source_document_id=source_document_id,
        extraction_result_id=extraction_result_id,
        draft_event_type=draft_event_type,
        draft_title=draft_title,
        draft_json=draft_json,
        missing_fields=missing_fields,
        confidence_level=confidence_level,
        safety_flags=safety_flags,
        status=status,
        expires_at=expires_at,
    )
    db.add(draft)
    db.flush()
    return draft


def get_medical_event_draft(
    db: Session,
    draft_id: UUID,
) -> MedicalEventDraft | None:
    return db.get(MedicalEventDraft, draft_id)


def list_pending_medical_event_drafts(
    db: Session,
    user_id: UUID,
    *,
    family_id: UUID | None = None,
    limit: int = 50,
) -> list[MedicalEventDraft]:
    stmt = select(MedicalEventDraft).where(
        MedicalEventDraft.user_id == user_id,
        MedicalEventDraft.status == MedicalEventDraftStatus.PENDING,
    )
    if family_id is not None:
        stmt = stmt.where(MedicalEventDraft.family_id == family_id)
    return list(db.scalars(stmt.order_by(MedicalEventDraft.created_at.desc()).limit(limit)))


def update_medical_event_draft_status(
    db: Session,
    draft_id: UUID,
    status: MedicalEventDraftStatus,
    *,
    confirmed_event_id: UUID | None = None,
    confirmed_at: datetime | None = None,
) -> MedicalEventDraft | None:
    draft = get_medical_event_draft(db, draft_id)
    if draft is None:
        return None
    draft.status = status
    if confirmed_event_id is not None:
        draft.confirmed_event_id = confirmed_event_id
    if confirmed_at is not None:
        draft.confirmed_at = confirmed_at
    db.flush()
    return draft
