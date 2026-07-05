from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.access_control import require_self_or_family_permission
from app.api.deps import get_current_user_id_for_demo, get_db
from app.modules.alerts import service
from app.modules.alerts.api_schemas import AlertCreateRequest, AlertResponse, AlertTransitionRequest
from app.modules.alerts.exceptions import AlertNotFoundError, InvalidAlertError, InvalidAlertTransitionError


router = APIRouter(tags=["alerts"])


@router.post("/alerts/me", response_model=AlertResponse, status_code=201)
def create_my_alert(payload: AlertCreateRequest, current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    return _create_alert(db, user_id=current_user_id, family_id=None, created_by_user_id=current_user_id, payload=payload)


@router.get("/alerts/me/active")
def get_my_active_alerts(current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    return {"items": [_alert_response(alert) for alert in service.get_active_alerts(db, user_id=current_user_id)]}


@router.get("/alerts/me/due")
def get_my_due_alerts(due_before: datetime | None = None, current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    return {"items": [_alert_response(alert) for alert in service.get_due_alerts(db, user_id=current_user_id, due_before=due_before)]}


@router.get("/alerts/me/summary")
def get_my_alert_summary(current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    return service.get_alert_summary(db, user_id=current_user_id)


@router.post("/alerts/me/{alert_id}/read", response_model=AlertResponse)
def read_my_alert(alert_id: UUID, current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    _assert_alert_scope(_get_alert_or_404(db, alert_id), user_id=current_user_id, family_id=None)
    return _transition(lambda: service.mark_alert_read(db, alert_id, actor_user_id=current_user_id))


@router.post("/alerts/me/{alert_id}/resolve", response_model=AlertResponse)
def resolve_my_alert(alert_id: UUID, payload: AlertTransitionRequest | None = None, current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    _assert_alert_scope(_get_alert_or_404(db, alert_id), user_id=current_user_id, family_id=None)
    return _transition(lambda: service.resolve_alert(db, alert_id, actor_user_id=current_user_id, note=payload.note if payload else None))


@router.post("/alerts/me/{alert_id}/dismiss", response_model=AlertResponse)
def dismiss_my_alert(alert_id: UUID, payload: AlertTransitionRequest | None = None, current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    _assert_alert_scope(_get_alert_or_404(db, alert_id), user_id=current_user_id, family_id=None)
    return _transition(lambda: service.dismiss_alert(db, alert_id, actor_user_id=current_user_id, note=payload.note if payload else None))


@router.post("/alerts/me/{alert_id}/reopen", response_model=AlertResponse)
def reopen_my_alert(alert_id: UUID, payload: AlertTransitionRequest | None = None, current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    _assert_alert_scope(_get_alert_or_404(db, alert_id), user_id=current_user_id, family_id=None)
    return _transition(lambda: service.reopen_alert(db, alert_id, actor_user_id=current_user_id, note=payload.note if payload else None))


@router.post("/alerts/me/{alert_id}/expire", response_model=AlertResponse)
def expire_my_alert(alert_id: UUID, current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    _assert_alert_scope(_get_alert_or_404(db, alert_id), user_id=current_user_id, family_id=None)
    return _transition(lambda: service.expire_alert(db, alert_id))


@router.get("/families/{family_id}/members/{target_user_id}/alerts/active")
def get_family_member_active_alerts(family_id: UUID, target_user_id: UUID, current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    _require_permission(db, current_user_id, family_id, target_user_id, "alerts", "view")
    return {"items": [_alert_response(alert) for alert in service.get_active_alerts(db, user_id=target_user_id, family_id=family_id)]}


@router.get("/families/{family_id}/members/{target_user_id}/alerts/summary")
def get_family_member_alert_summary(family_id: UUID, target_user_id: UUID, current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    _require_permission(db, current_user_id, family_id, target_user_id, "alerts", "view")
    return service.get_alert_summary(db, user_id=target_user_id, family_id=family_id)


@router.post("/families/{family_id}/members/{target_user_id}/alerts", response_model=AlertResponse, status_code=201)
def create_family_member_alert(
    family_id: UUID,
    target_user_id: UUID,
    payload: AlertCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    # Phase 08.A split alert creation from alerts:view. Family alert writes now
    # require alerts:create / can_create_alerts while preserving the route path.
    _require_permission(db, current_user_id, family_id, target_user_id, "alerts", "create")
    return _create_alert(db, user_id=target_user_id, family_id=family_id, created_by_user_id=current_user_id, payload=payload)


def _create_alert(db: Session, *, user_id: UUID, family_id: UUID | None, created_by_user_id: UUID, payload: AlertCreateRequest) -> dict:
    try:
        alert = service.create_alert(db, user_id=user_id, family_id=family_id, created_by_user_id=created_by_user_id, **payload.model_dump())
    except (InvalidAlertError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _alert_response(alert)


def _get_alert_or_404(db: Session, alert_id: UUID):
    try:
        return service.get_alert(db, alert_id)
    except AlertNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _assert_alert_scope(alert, *, user_id: UUID, family_id: UUID | None) -> None:
    if alert.user_id != user_id or alert.family_id != family_id:
        raise HTTPException(status_code=404, detail="alert not found")


def _transition(fn) -> dict:
    try:
        return _alert_response(fn())
    except InvalidAlertTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def _require_permission(db: Session, current_user_id: UUID, family_id: UUID, target_user_id: UUID, permission_type: str, action: str) -> None:
    require_self_or_family_permission(
        db,
        current_user_id=current_user_id,
        family_id=family_id,
        target_user_id=target_user_id,
        permission_type=permission_type,
        action=action,
        data_category="alerts",
        access_reason="api_alerts",
    )


def _alert_response(alert) -> dict:
    return {
        "id": alert.id,
        "user_id": alert.user_id,
        "family_id": alert.family_id,
        "created_by_user_id": alert.created_by_user_id,
        "alert_type": _enum_value(alert.alert_type),
        "level": _enum_value(alert.level),
        "title": alert.title,
        "message": alert.message,
        "suggested_action": alert.suggested_action,
        "related_entity_type": alert.related_entity_type,
        "related_entity_id": alert.related_entity_id,
        "trigger_reason": alert.trigger_reason,
        "status": _enum_value(alert.status),
        "due_at": alert.due_at,
        "resolved_at": alert.resolved_at,
        "source": _enum_value(alert.source),
        "created_at": alert.created_at,
        "updated_at": alert.updated_at,
    }


def _enum_value(value):
    return value.value if hasattr(value, "value") else value
