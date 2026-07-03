from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id_for_demo, get_db
from app.modules.document_center import service as document_service
from app.modules.document_center.exceptions import MedicalDocumentNotFoundError
from app.modules.document_processing import service
from app.modules.document_processing.api_schemas import (
    ExtractionResultCreateRequest,
    MedicalEventDraftCreateRequest,
    MedicalEventDraftResponse,
    ProcessingJobCreateRequest,
    ProcessingJobFailedRequest,
    ProcessingJobResponse,
)
from app.modules.document_processing.exceptions import (
    DocumentExtractionResultNotFoundError,
    DocumentProcessingJobNotFoundError,
    InvalidMedicalEventDraftError,
    MedicalEventDraftNotFoundError,
    MedicalEventDraftNotPendingError,
)
from app.modules.permissions import service as permission_service


router = APIRouter(tags=["document-processing"])


@router.post(
    "/document-processing/me/documents/{document_id}/jobs",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_my_processing_job(
    document_id: UUID,
    payload: ProcessingJobCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    document = _get_document_or_404(db, document_id)
    _assert_document_scope(document, user_id=current_user_id, family_id=None)
    job = service.create_processing_job(db, document_id=document_id, user_id=current_user_id, family_id=None, job_type=payload.job_type)
    return _job_response(job)


@router.post("/document-processing/me/jobs/{job_id}/started", response_model=ProcessingJobResponse)
def mark_my_job_started(job_id: UUID, current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    _assert_job_scope(_get_job_or_404(db, job_id), user_id=current_user_id, family_id=None)
    return _job_response(service.mark_job_started(db, job_id))


@router.post("/document-processing/me/jobs/{job_id}/success", response_model=ProcessingJobResponse)
def mark_my_job_success(job_id: UUID, current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    _assert_job_scope(_get_job_or_404(db, job_id), user_id=current_user_id, family_id=None)
    return _job_response(service.mark_job_success(db, job_id))


@router.post("/document-processing/me/jobs/{job_id}/failed", response_model=ProcessingJobResponse)
def mark_my_job_failed(
    job_id: UUID,
    payload: ProcessingJobFailedRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _assert_job_scope(_get_job_or_404(db, job_id), user_id=current_user_id, family_id=None)
    return _job_response(service.mark_job_failed(db, job_id, payload.error_message))


@router.post("/document-processing/me/documents/{document_id}/extraction-results", status_code=status.HTTP_201_CREATED)
def save_my_extraction_result(
    document_id: UUID,
    payload: ExtractionResultCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    document = _get_document_or_404(db, document_id)
    _assert_document_scope(document, user_id=current_user_id, family_id=None)
    return _save_extraction_result(db, document_id=document_id, user_id=current_user_id, family_id=None, payload=payload)


@router.post("/document-processing/me/event-drafts", response_model=MedicalEventDraftResponse, status_code=status.HTTP_201_CREATED)
def create_my_event_draft(
    payload: MedicalEventDraftCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    return _create_draft(db, user_id=current_user_id, family_id=None, created_by_user_id=current_user_id, payload=payload)


@router.get("/document-processing/me/event-drafts/pending")
def list_my_pending_event_drafts(current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    return {"items": [_draft_response(draft) for draft in service.list_pending_medical_event_drafts(db, user_id=current_user_id)]}


@router.post("/document-processing/me/event-drafts/{draft_id}/confirm")
def confirm_my_event_draft(draft_id: UUID, current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    draft = _get_draft_or_404(db, draft_id)
    _assert_draft_scope(draft, user_id=current_user_id, family_id=None)
    return _confirm_draft(db, draft_id=draft_id, confirmed_by_user_id=current_user_id)


@router.post("/document-processing/me/event-drafts/{draft_id}/cancel", response_model=MedicalEventDraftResponse)
def cancel_my_event_draft(draft_id: UUID, current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    draft = _get_draft_or_404(db, draft_id)
    _assert_draft_scope(draft, user_id=current_user_id, family_id=None)
    return _draft_response(service.cancel_medical_event_draft(db, draft_id))


@router.post(
    "/families/{family_id}/members/{target_user_id}/document-processing/documents/{document_id}/jobs",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_family_member_processing_job(
    family_id: UUID,
    target_user_id: UUID,
    document_id: UUID,
    payload: ProcessingJobCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "documents", "create")
    document = _get_document_or_404(db, document_id)
    _assert_document_scope(document, user_id=target_user_id, family_id=family_id)
    job = service.create_processing_job(db, document_id=document_id, user_id=target_user_id, family_id=family_id, job_type=payload.job_type)
    return _job_response(job)


@router.post("/families/{family_id}/members/{target_user_id}/document-processing/extraction-results", status_code=status.HTTP_201_CREATED)
def save_family_member_extraction_result(
    family_id: UUID,
    target_user_id: UUID,
    payload: ExtractionResultCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "documents", "create")
    if payload.processing_job_id is not None:
        _assert_job_scope(_get_job_or_404(db, payload.processing_job_id), user_id=target_user_id, family_id=family_id)
    if payload.processing_job_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="processing_job_id is required for family extraction results")
    job = _get_job_or_404(db, payload.processing_job_id)
    return _save_extraction_result(db, document_id=job.document_id, user_id=target_user_id, family_id=family_id, payload=payload)


@router.post(
    "/families/{family_id}/members/{target_user_id}/document-processing/event-drafts",
    response_model=MedicalEventDraftResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_family_member_event_draft(
    family_id: UUID,
    target_user_id: UUID,
    payload: MedicalEventDraftCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "documents", "create")
    return _create_draft(db, user_id=target_user_id, family_id=family_id, created_by_user_id=current_user_id, payload=payload)


@router.get("/families/{family_id}/members/{target_user_id}/document-processing/event-drafts/pending")
def list_family_member_pending_event_drafts(
    family_id: UUID,
    target_user_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "documents", "view")
    return {"items": [_draft_response(draft) for draft in service.list_pending_medical_event_drafts(db, user_id=target_user_id, family_id=family_id)]}


@router.post("/families/{family_id}/members/{target_user_id}/document-processing/event-drafts/{draft_id}/confirm")
def confirm_family_member_event_draft(
    family_id: UUID,
    target_user_id: UUID,
    draft_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "documents", "create")
    _require_permission(db, current_user_id, family_id, target_user_id, "medical_events", "create")
    draft = _get_draft_or_404(db, draft_id)
    _assert_draft_scope(draft, user_id=target_user_id, family_id=family_id)
    return _confirm_draft(db, draft_id=draft_id, confirmed_by_user_id=current_user_id)


def _save_extraction_result(db: Session, *, document_id: UUID, user_id: UUID, family_id: UUID | None, payload: ExtractionResultCreateRequest) -> dict:
    try:
        result = service.save_extraction_result(db, document_id=document_id, user_id=user_id, family_id=family_id, **payload.model_dump())
    except ValueError as exc:
        raise _bad_request(exc) from exc
    return _extraction_response(result)


def _create_draft(db: Session, *, user_id: UUID, family_id: UUID | None, created_by_user_id: UUID, payload: MedicalEventDraftCreateRequest) -> dict:
    _assert_draft_references_scope(db, user_id=user_id, family_id=family_id, payload=payload)
    try:
        draft = service.create_medical_event_draft(db, user_id=user_id, family_id=family_id, created_by_user_id=created_by_user_id, **payload.model_dump())
    except (InvalidMedicalEventDraftError, ValueError) as exc:
        raise _bad_request(exc) from exc
    return _draft_response(draft)


def _confirm_draft(db: Session, *, draft_id: UUID, confirmed_by_user_id: UUID) -> dict:
    try:
        event = service.confirm_medical_event_draft(db, draft_id=draft_id, confirmed_by_user_id=confirmed_by_user_id)
    except MedicalEventDraftNotPendingError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvalidMedicalEventDraftError as exc:
        raise _bad_request(exc) from exc
    return _event_response(event)


def _get_document_or_404(db: Session, document_id: UUID):
    try:
        return document_service.get_document(db, document_id)
    except MedicalDocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def _get_job_or_404(db: Session, job_id: UUID):
    try:
        return service.get_processing_job(db, job_id)
    except DocumentProcessingJobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def _get_draft_or_404(db: Session, draft_id: UUID):
    try:
        return service.get_medical_event_draft(db, draft_id)
    except MedicalEventDraftNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def _get_extraction_result_or_404(db: Session, result_id: UUID):
    try:
        return service.get_extraction_result(db, result_id)
    except DocumentExtractionResultNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def _assert_document_scope(document, *, user_id: UUID, family_id: UUID | None) -> None:
    if document.user_id != user_id or document.family_id != family_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="medical document not found")


def _assert_job_scope(job, *, user_id: UUID, family_id: UUID | None) -> None:
    if job.user_id != user_id or job.family_id != family_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document processing job not found")


def _assert_draft_scope(draft, *, user_id: UUID, family_id: UUID | None) -> None:
    if draft.user_id != user_id or draft.family_id != family_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="medical event draft not found")


def _assert_extraction_result_scope(result, *, user_id: UUID, family_id: UUID | None) -> None:
    if result.user_id != user_id or result.family_id != family_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document extraction result not found")


def _assert_draft_references_scope(db: Session, *, user_id: UUID, family_id: UUID | None, payload: MedicalEventDraftCreateRequest) -> None:
    if payload.source_document_id is not None:
        document = _get_document_or_404(db, payload.source_document_id)
        _assert_document_scope(document, user_id=user_id, family_id=family_id)
    if payload.extraction_result_id is not None:
        result = _get_extraction_result_or_404(db, payload.extraction_result_id)
        _assert_extraction_result_scope(result, user_id=user_id, family_id=family_id)


def _require_permission(db: Session, current_user_id: UUID, family_id: UUID, target_user_id: UUID, permission_type: str, action: str) -> None:
    result = permission_service.check_member_permission(
        db,
        current_user_id=current_user_id,
        family_id=family_id,
        target_user_id=target_user_id,
        permission_type=permission_type,
        action=action,
    )
    if not result.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result.safe_message)


def _job_response(job) -> dict:
    return {
        "id": job.id,
        "document_id": job.document_id,
        "user_id": job.user_id,
        "family_id": job.family_id,
        "job_type": _enum_value(job.job_type),
        "status": _enum_value(job.status),
        "attempt_count": job.attempt_count,
        "error_message": job.error_message,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


def _extraction_response(result) -> dict:
    excerpt = result.raw_extracted_text[:120] if result.raw_extracted_text else None
    return {
        "id": result.id,
        "document_id": result.document_id,
        "processing_job_id": result.processing_job_id,
        "user_id": result.user_id,
        "family_id": result.family_id,
        "extraction_mode": _enum_value(result.extraction_mode),
        "ai_summary": result.ai_summary,
        "key_findings": result.key_findings,
        "doctor_advice": result.doctor_advice,
        "suggested_events": result.suggested_events,
        "confidence_level": _enum_value(result.confidence_level),
        "safety_notes": result.safety_notes,
        "status": _enum_value(result.status),
        "raw_text_excerpt": excerpt,
        "created_at": result.created_at,
        "updated_at": result.updated_at,
    }


def _draft_response(draft) -> dict:
    return {
        "id": draft.id,
        "user_id": draft.user_id,
        "family_id": draft.family_id,
        "created_by_user_id": draft.created_by_user_id,
        "source_document_id": draft.source_document_id,
        "extraction_result_id": draft.extraction_result_id,
        "draft_event_type": _enum_value(draft.draft_event_type),
        "draft_title": draft.draft_title,
        "draft_json": draft.draft_json,
        "missing_fields": draft.missing_fields,
        "confidence_level": _enum_value(draft.confidence_level),
        "safety_flags": draft.safety_flags,
        "status": _enum_value(draft.status),
        "confirmed_event_id": draft.confirmed_event_id,
        "confirmed_at": draft.confirmed_at,
        "expires_at": draft.expires_at,
        "created_at": draft.created_at,
        "updated_at": draft.updated_at,
    }


def _event_response(event) -> dict:
    return {
        "id": event.id,
        "user_id": event.user_id,
        "family_id": event.family_id,
        "created_by_user_id": event.created_by_user_id,
        "event_type": _enum_value(event.event_type),
        "title": event.title,
        "event_date": event.event_date,
        "event_date_text": event.event_date_text,
        "hospital_or_org": event.hospital_or_org,
        "department": event.department,
        "diagnosis_text": event.diagnosis_text,
        "summary": event.summary,
        "doctor_advice": event.doctor_advice,
        "medications": event.medications,
        "key_findings": event.key_findings,
        "follow_up_needed": event.follow_up_needed,
        "follow_up_at": event.follow_up_at,
        "related_document_id": event.related_document_id,
        "source": _enum_value(event.source),
        "confidence_level": _enum_value(event.confidence_level),
        "timeline_visible": event.timeline_visible,
        "status": _enum_value(event.status),
        "created_at": event.created_at,
        "updated_at": event.updated_at,
    }


def _enum_value(value):
    return value.value if hasattr(value, "value") else value


def _bad_request(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
