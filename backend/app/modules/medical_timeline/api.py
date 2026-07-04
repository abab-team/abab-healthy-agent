from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.access_control import require_self_or_family_permission
from app.api.deps import get_current_user_id_for_demo, get_db
from app.modules.medical_timeline import service
from app.modules.medical_timeline.api_schemas import (
    MedicalEventCreateRequest,
    MedicalEventResponse,
)
from app.modules.medical_timeline.exceptions import InvalidMedicalEventError, MedicalEventNotFoundError


router = APIRouter(tags=["medical-timeline"])


@router.post("/medical-timeline/me/events", response_model=MedicalEventResponse, status_code=status.HTTP_201_CREATED)
def create_my_medical_event(
    payload: MedicalEventCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    return _create_event(db, user_id=current_user_id, family_id=None, created_by_user_id=current_user_id, payload=payload)


@router.get("/medical-timeline/me/events")
def get_my_medical_events(
    days: int = Query(default=365, ge=1, le=365),
    event_type: str | None = None,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    try:
        events = service.get_medical_timeline(db, user_id=current_user_id, days=days, event_type=event_type)
    except ValueError as exc:
        raise _bad_request(exc) from exc
    return {"items": [_event_response(event) for event in events]}


@router.get("/medical-timeline/me/events/summary")
def get_my_medical_event_summary(
    days: int = Query(default=365, ge=1, le=365),
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    return service.get_medical_event_summary(db, user_id=current_user_id, days=days)


@router.get("/medical-timeline/me/events/follow-ups")
def get_my_follow_up_events(
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    return {"items": [_event_response(event) for event in service.get_follow_up_events(db, user_id=current_user_id)]}


@router.post("/medical-timeline/me/events/{event_id}/archive", response_model=MedicalEventResponse)
def archive_my_medical_event(
    event_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    event = _get_event_or_404(db, event_id)
    _assert_event_scope(event, user_id=current_user_id, family_id=None)
    try:
        return _event_response(service.archive_medical_event(db, event_id))
    except MedicalEventNotFoundError as exc:
        raise _not_found(exc) from exc


@router.post(
    "/families/{family_id}/members/{target_user_id}/medical-timeline/events",
    response_model=MedicalEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_family_member_medical_event(
    family_id: UUID,
    target_user_id: UUID,
    payload: MedicalEventCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "medical_events", "create")
    return _create_event(db, user_id=target_user_id, family_id=family_id, created_by_user_id=current_user_id, payload=payload)


@router.get("/families/{family_id}/members/{target_user_id}/medical-timeline/events")
def get_family_member_medical_events(
    family_id: UUID,
    target_user_id: UUID,
    days: int = Query(default=365, ge=1, le=365),
    event_type: str | None = None,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "medical_events", "view")
    try:
        events = service.get_medical_timeline(db, user_id=target_user_id, family_id=family_id, days=days, event_type=event_type)
    except ValueError as exc:
        raise _bad_request(exc) from exc
    return {"items": [_event_response(event) for event in events]}


@router.get("/families/{family_id}/members/{target_user_id}/medical-timeline/events/summary")
def get_family_member_medical_event_summary(
    family_id: UUID,
    target_user_id: UUID,
    days: int = Query(default=365, ge=1, le=365),
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "medical_events", "view")
    return service.get_medical_event_summary(db, user_id=target_user_id, family_id=family_id, days=days)


@router.get("/families/{family_id}/members/{target_user_id}/medical-timeline/events/follow-ups")
def get_family_member_follow_up_events(
    family_id: UUID,
    target_user_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "medical_events", "view")
    return {"items": [_event_response(event) for event in service.get_follow_up_events(db, user_id=target_user_id, family_id=family_id)]}


def _create_event(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID | None,
    created_by_user_id: UUID,
    payload: MedicalEventCreateRequest,
) -> dict:
    try:
        event = service.create_medical_event(
            db,
            user_id=user_id,
            family_id=family_id,
            created_by_user_id=created_by_user_id,
            **payload.model_dump(),
        )
    except (InvalidMedicalEventError, ValueError) as exc:
        raise _bad_request(exc) from exc
    return _event_response(event)


def _get_event_or_404(db: Session, event_id: UUID):
    try:
        return service.get_medical_event(db, event_id)
    except MedicalEventNotFoundError as exc:
        raise _not_found(exc) from exc


def _assert_event_scope(event, *, user_id: UUID, family_id: UUID | None) -> None:
    if event.user_id != user_id or event.family_id != family_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="medical event not found")


def _require_permission(db: Session, current_user_id: UUID, family_id: UUID, target_user_id: UUID, permission_type: str, action: str) -> None:
    require_self_or_family_permission(
        db,
        current_user_id=current_user_id,
        family_id=family_id,
        target_user_id=target_user_id,
        permission_type=permission_type,
        action=action,
        data_category="medical_events",
        access_reason="api_medical_timeline",
    )


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


def _not_found(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
