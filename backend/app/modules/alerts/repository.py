from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.alerts.enums import (
    AlertEventType,
    AlertLevel,
    AlertSource,
    AlertStatus,
    AlertType,
)
from app.modules.alerts.models import Alert, AlertEvent


_UNSET = object()


def create_alert(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID | None = None,
    created_by_user_id: UUID | None = None,
    alert_type: AlertType,
    level: AlertLevel,
    title: str,
    message: str,
    suggested_action: str | None = None,
    related_entity_type: str | None = None,
    related_entity_id: UUID | None = None,
    trigger_reason: str | None = None,
    status: AlertStatus = AlertStatus.ACTIVE,
    due_at: datetime | None = None,
    resolved_at: datetime | None = None,
    source: AlertSource = AlertSource.SYSTEM,
) -> Alert:
    alert = Alert(
        user_id=user_id,
        family_id=family_id,
        created_by_user_id=created_by_user_id,
        alert_type=alert_type,
        level=level,
        title=title,
        message=message,
        suggested_action=suggested_action,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        trigger_reason=trigger_reason,
        status=status,
        due_at=due_at,
        resolved_at=resolved_at,
        source=source,
    )
    db.add(alert)
    db.flush()
    return alert


def get_alert(db: Session, alert_id: UUID) -> Alert | None:
    return db.get(Alert, alert_id)


def list_alerts(
    db: Session,
    user_id: UUID,
    *,
    family_id: UUID | None | object = _UNSET,
    status: AlertStatus | None = None,
    alert_type: AlertType | None = None,
    level: AlertLevel | None = None,
    limit: int = 100,
) -> list[Alert]:
    stmt = select(Alert).where(Alert.user_id == user_id)
    if family_id is not _UNSET:
        stmt = stmt.where(Alert.family_id == family_id)
    if status is not None:
        stmt = stmt.where(Alert.status == status)
    if alert_type is not None:
        stmt = stmt.where(Alert.alert_type == alert_type)
    if level is not None:
        stmt = stmt.where(Alert.level == level)
    return list(db.scalars(stmt.order_by(Alert.created_at.desc()).limit(limit)))


def list_active_alerts(
    db: Session,
    user_id: UUID,
    *,
    family_id: UUID | None | object = _UNSET,
    limit: int = 50,
) -> list[Alert]:
    stmt = (
        select(Alert)
        .where(Alert.user_id == user_id, Alert.status == AlertStatus.ACTIVE)
        .order_by(Alert.created_at.desc())
        .limit(limit)
    )
    if family_id is not _UNSET:
        stmt = stmt.where(Alert.family_id == family_id)
    return list(db.scalars(stmt))


def list_due_alerts(
    db: Session,
    *,
    user_id: UUID | None = None,
    family_id: UUID | None | object = _UNSET,
    due_before: datetime | None = None,
    status: AlertStatus = AlertStatus.ACTIVE,
    limit: int = 100,
) -> list[Alert]:
    due_before = due_before or datetime.now(timezone.utc)
    stmt = select(Alert).where(Alert.status == status, Alert.due_at <= due_before)
    if user_id is not None:
        stmt = stmt.where(Alert.user_id == user_id)
    if family_id is not _UNSET:
        stmt = stmt.where(Alert.family_id == family_id)
    return list(db.scalars(stmt.order_by(Alert.due_at.asc()).limit(limit)))


def update_alert_status(
    db: Session,
    alert_id: UUID,
    status: AlertStatus,
    *,
    resolved_at: datetime | None = None,
) -> Alert | None:
    alert = get_alert(db, alert_id)
    if alert is None:
        return None
    alert.status = status
    alert.resolved_at = resolved_at if status == AlertStatus.RESOLVED else None
    db.flush()
    return alert


def update_alert(db: Session, alert_id: UUID, **fields) -> Alert | None:
    alert = get_alert(db, alert_id)
    if alert is None:
        return None
    for key, value in fields.items():
        setattr(alert, key, value)
    db.flush()
    return alert


def create_alert_event(
    db: Session,
    *,
    alert_id: UUID,
    actor_user_id: UUID | None = None,
    event_type: AlertEventType,
    before_status: AlertStatus | None = None,
    after_status: AlertStatus | None = None,
    note: str | None = None,
) -> AlertEvent:
    event = AlertEvent(
        alert_id=alert_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        before_status=before_status,
        after_status=after_status,
        note=note,
    )
    db.add(event)
    db.flush()
    return event


def list_alert_events(db: Session, alert_id: UUID) -> list[AlertEvent]:
    stmt = (
        select(AlertEvent)
        .where(AlertEvent.alert_id == alert_id)
        .order_by(AlertEvent.created_at.asc())
    )
    return list(db.scalars(stmt))
