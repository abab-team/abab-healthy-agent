from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id_for_demo, get_db
from app.modules.health_record import service
from app.modules.health_record.api_schemas import (
    HealthRecordDraftCreateRequest,
    HealthRecordDraftResponse,
    SymptomCreateRequest,
    SymptomRecordResponse,
)
from app.modules.health_record.enums import HealthRecordDraftStatus
from app.modules.health_record.exceptions import (
    HealthRecordDraftNotFoundError,
    HealthRecordDraftNotPendingError,
    HealthRecordDraftTypeUnsupportedError,
    InvalidHealthRecordDraftError,
)
from app.modules.permissions import service as permission_service


router = APIRouter(tags=["health-records"])


@router.post(
    "/health-records/me/symptoms",
    response_model=SymptomRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_my_symptom(
    payload: SymptomCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    return _create_symptom(
        db,
        user_id=current_user_id,
        created_by_user_id=current_user_id,
        family_id=None,
        payload=payload,
    )


@router.get("/health-records/me/symptoms/recent")
def get_my_recent_symptoms(
    days: int = Query(default=30, ge=1, le=365),
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    return {
        "items": [
            _symptom_response(record)
            for record in service.get_recent_symptoms(db, user_id=current_user_id, family_id=None, days=days)
        ]
    }


@router.get("/health-records/me/symptoms/summary")
def get_my_symptom_summary(
    days: int = Query(default=30, ge=1, le=365),
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    return service.get_symptom_summary(db, user_id=current_user_id, family_id=None, days=days)


@router.post(
    "/health-records/me/drafts",
    response_model=HealthRecordDraftResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_my_draft(
    payload: HealthRecordDraftCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    return _create_draft(
        db,
        user_id=current_user_id,
        created_by_user_id=current_user_id,
        family_id=None,
        payload=payload,
    )


@router.get("/health-records/me/drafts/pending")
def get_my_pending_drafts(
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    return {
        "items": [
            _draft_response(draft)
            for draft in service.list_pending_drafts(db, user_id=current_user_id, family_id=None)
        ]
    }


@router.post(
    "/health-records/me/drafts/{draft_id}/confirm",
    response_model=SymptomRecordResponse,
)
def confirm_my_draft(
    draft_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    draft = _get_draft_or_404(db, draft_id)
    _assert_draft_scope(draft, user_id=current_user_id, family_id=None)
    return _confirm_draft(db, draft_id=draft_id, confirmed_by_user_id=current_user_id)


@router.post(
    "/health-records/me/drafts/{draft_id}/cancel",
    response_model=HealthRecordDraftResponse,
)
def cancel_my_draft(
    draft_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    draft = _get_draft_or_404(db, draft_id)
    _assert_draft_scope(draft, user_id=current_user_id, family_id=None)
    _assert_pending(draft)
    return _draft_response(service.cancel_draft(db, draft_id))


@router.post(
    "/families/{family_id}/members/{target_user_id}/health-records/symptoms",
    response_model=SymptomRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_family_member_symptom(
    family_id: UUID,
    target_user_id: UUID,
    payload: SymptomCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "symptoms", "create")
    return _create_symptom(
        db,
        user_id=target_user_id,
        created_by_user_id=current_user_id,
        family_id=family_id,
        payload=payload,
    )


@router.get("/families/{family_id}/members/{target_user_id}/health-records/symptoms/recent")
def get_family_member_recent_symptoms(
    family_id: UUID,
    target_user_id: UUID,
    days: int = Query(default=30, ge=1, le=365),
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "symptoms", "view")
    return {
        "items": [
            _symptom_response(record)
            for record in service.get_recent_symptoms(db, user_id=target_user_id, family_id=family_id, days=days)
        ]
    }


@router.get("/families/{family_id}/members/{target_user_id}/health-records/symptoms/summary")
def get_family_member_symptom_summary(
    family_id: UUID,
    target_user_id: UUID,
    days: int = Query(default=30, ge=1, le=365),
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "symptoms", "view")
    return service.get_symptom_summary(db, user_id=target_user_id, family_id=family_id, days=days)


@router.post(
    "/families/{family_id}/members/{target_user_id}/health-records/drafts",
    response_model=HealthRecordDraftResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_family_member_draft(
    family_id: UUID,
    target_user_id: UUID,
    payload: HealthRecordDraftCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "symptoms", "create")
    return _create_draft(
        db,
        user_id=target_user_id,
        created_by_user_id=current_user_id,
        family_id=family_id,
        payload=payload,
    )


@router.get("/families/{family_id}/members/{target_user_id}/health-records/drafts/pending")
def get_family_member_pending_drafts(
    family_id: UUID,
    target_user_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "symptoms", "view")
    return {
        "items": [
            _draft_response(draft)
            for draft in service.list_pending_drafts(
                db,
                user_id=target_user_id,
                family_id=family_id,
            )
        ]
    }


@router.post(
    "/families/{family_id}/members/{target_user_id}/health-records/drafts/{draft_id}/confirm",
    response_model=SymptomRecordResponse,
)
def confirm_family_member_draft(
    family_id: UUID,
    target_user_id: UUID,
    draft_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "symptoms", "create")
    draft = _get_draft_or_404(db, draft_id)
    _assert_draft_scope(draft, user_id=target_user_id, family_id=family_id)
    return _confirm_draft(db, draft_id=draft_id, confirmed_by_user_id=current_user_id)


@router.post(
    "/families/{family_id}/members/{target_user_id}/health-records/drafts/{draft_id}/cancel",
    response_model=HealthRecordDraftResponse,
)
def cancel_family_member_draft(
    family_id: UUID,
    target_user_id: UUID,
    draft_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "symptoms", "create")
    draft = _get_draft_or_404(db, draft_id)
    _assert_draft_scope(draft, user_id=target_user_id, family_id=family_id)
    _assert_pending(draft)
    return _draft_response(service.cancel_draft(db, draft_id))


def _create_symptom(
    db: Session,
    *,
    user_id: UUID,
    created_by_user_id: UUID,
    family_id: UUID | None,
    payload: SymptomCreateRequest,
) -> dict:
    try:
        record = service.create_symptom_record(
            db,
            user_id=user_id,
            family_id=family_id,
            created_by_user_id=created_by_user_id,
            **payload.model_dump(),
        )
    except (InvalidHealthRecordDraftError, ValueError) as exc:
        raise _bad_request(exc) from exc
    return _symptom_response(record)


def _create_draft(
    db: Session,
    *,
    user_id: UUID,
    created_by_user_id: UUID,
    family_id: UUID | None,
    payload: HealthRecordDraftCreateRequest,
) -> dict:
    try:
        draft = service.create_health_record_draft(
            db,
            user_id=user_id,
            family_id=family_id,
            created_by_user_id=created_by_user_id,
            **payload.model_dump(),
        )
    except (InvalidHealthRecordDraftError, ValueError) as exc:
        raise _bad_request(exc) from exc
    return _draft_response(draft)


def _confirm_draft(
    db: Session,
    *,
    draft_id: UUID,
    confirmed_by_user_id: UUID,
) -> dict:
    try:
        record = service.confirm_symptom_draft(
            db,
            draft_id=draft_id,
            confirmed_by_user_id=confirmed_by_user_id,
        )
    except HealthRecordDraftNotPendingError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except HealthRecordDraftTypeUnsupportedError as exc:
        raise _bad_request(exc) from exc
    return _symptom_response(record)


def _get_draft_or_404(db: Session, draft_id: UUID):
    try:
        return service.get_health_record_draft(db, draft_id)
    except HealthRecordDraftNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def _assert_draft_scope(draft, *, user_id: UUID, family_id: UUID | None) -> None:
    if draft.user_id != user_id or draft.family_id != family_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="draft not found")


def _assert_pending(draft) -> None:
    if draft.status != HealthRecordDraftStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="only pending drafts can be changed",
        )


def _require_permission(
    db: Session,
    current_user_id: UUID,
    family_id: UUID,
    target_user_id: UUID,
    permission_type: str,
    action: str,
) -> None:
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


def _symptom_response(record) -> dict:
    return {
        "id": record.id,
        "user_id": record.user_id,
        "family_id": record.family_id,
        "created_by_user_id": record.created_by_user_id,
        "raw_text": record.raw_text,
        "symptom_name": record.symptom_name,
        "body_part": record.body_part,
        "severity": record.severity,
        "started_at": record.started_at,
        "ended_at": record.ended_at,
        "possible_trigger": record.possible_trigger,
        "follow_up_needed": record.follow_up_needed,
        "follow_up_at": record.follow_up_at,
        "status": _enum_value(record.status),
        "confidence_level": _enum_value(record.confidence_level),
        "ai_summary": record.ai_summary,
        "source": _enum_value(record.source),
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def _draft_response(draft) -> dict:
    return {
        "id": draft.id,
        "user_id": draft.user_id,
        "family_id": draft.family_id,
        "created_by_user_id": draft.created_by_user_id,
        "target_display_name": draft.target_display_name,
        "raw_text": draft.raw_text,
        "draft_type": _enum_value(draft.draft_type),
        "extracted_json": draft.extracted_json,
        "missing_fields": draft.missing_fields,
        "safety_flags": draft.safety_flags,
        "confidence_level": _enum_value(draft.confidence_level),
        "status": _enum_value(draft.status),
        "confirmed_record_id": draft.confirmed_record_id,
        "created_at": draft.created_at,
        "updated_at": draft.updated_at,
    }


def _enum_value(value):
    return value.value if hasattr(value, "value") else value


def _bad_request(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
