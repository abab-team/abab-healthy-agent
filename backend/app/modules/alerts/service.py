from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.alerts import repository
from app.modules.alerts.enums import (
    AlertEventType,
    AlertLevel,
    AlertSource,
    AlertStatus,
    AlertType,
)
from app.modules.alerts.exceptions import (
    AlertNotFoundError,
    InvalidAlertError,
    InvalidAlertTransitionError,
)
from app.modules.alerts.models import Alert
from app.modules.alerts.schemas import AlertSummary


_UNSET = repository._UNSET


def create_alert(
    db: Session,
    *,
    user_id: UUID,
    alert_type: AlertType | str,
    level: AlertLevel | str,
    title: str,
    message: str,
    family_id: UUID | None = None,
    created_by_user_id: UUID | None = None,
    suggested_action: str | None = None,
    related_entity_type: str | None = None,
    related_entity_id: UUID | None = None,
    trigger_reason: str | None = None,
    due_at: datetime | None = None,
    source: AlertSource | str = AlertSource.SYSTEM,
) -> Alert:
    _validate_required_text(title, "title")
    _validate_required_text(message, "message")
    alert = repository.create_alert(
        db,
        user_id=user_id,
        family_id=family_id,
        created_by_user_id=created_by_user_id,
        alert_type=_coerce_enum(AlertType, alert_type),
        level=_coerce_enum(AlertLevel, level),
        title=title.strip(),
        message=message.strip(),
        suggested_action=suggested_action,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        trigger_reason=trigger_reason,
        status=AlertStatus.ACTIVE,
        due_at=due_at,
        source=_coerce_enum(AlertSource, source),
    )
    repository.create_alert_event(
        db,
        alert_id=alert.id,
        actor_user_id=created_by_user_id,
        event_type=AlertEventType.CREATED,
        after_status=AlertStatus.ACTIVE,
    )
    return alert


def get_alert(db: Session, alert_id: UUID) -> Alert:
    alert = repository.get_alert(db, alert_id)
    if alert is None:
        raise AlertNotFoundError("alert not found")
    return alert


def get_active_alerts(db: Session, *, user_id: UUID, family_id: UUID | None | object = _UNSET) -> list[Alert]:
    return repository.list_active_alerts(db, user_id, family_id=family_id)


def get_due_alerts(
    db: Session,
    *,
    user_id: UUID | None = None,
    family_id: UUID | None | object = _UNSET,
    due_before: datetime | None = None,
) -> list[Alert]:
    return repository.list_due_alerts(db, user_id=user_id, family_id=family_id, due_before=due_before)


def mark_alert_read(
    db: Session,
    alert_id: UUID,
    *,
    actor_user_id: UUID | None = None,
) -> Alert:
    return _transition(
        db,
        alert_id,
        to_status=AlertStatus.READ,
        event_type=AlertEventType.READ,
        actor_user_id=actor_user_id,
        allowed_from={AlertStatus.ACTIVE},
    )


def resolve_alert(
    db: Session,
    alert_id: UUID,
    *,
    actor_user_id: UUID | None = None,
    note: str | None = None,
) -> Alert:
    return _transition(
        db,
        alert_id,
        to_status=AlertStatus.RESOLVED,
        event_type=AlertEventType.RESOLVED,
        actor_user_id=actor_user_id,
        note=note,
        allowed_from={AlertStatus.ACTIVE, AlertStatus.READ},
        resolved_at=datetime.now(timezone.utc),
    )


def dismiss_alert(
    db: Session,
    alert_id: UUID,
    *,
    actor_user_id: UUID | None = None,
    note: str | None = None,
) -> Alert:
    return _transition(
        db,
        alert_id,
        to_status=AlertStatus.DISMISSED,
        event_type=AlertEventType.DISMISSED,
        actor_user_id=actor_user_id,
        note=note,
        allowed_from={AlertStatus.ACTIVE, AlertStatus.READ},
    )


def reopen_alert(
    db: Session,
    alert_id: UUID,
    *,
    actor_user_id: UUID | None = None,
    note: str | None = None,
) -> Alert:
    return _transition(
        db,
        alert_id,
        to_status=AlertStatus.ACTIVE,
        event_type=AlertEventType.REOPENED,
        actor_user_id=actor_user_id,
        note=note,
        allowed_from={AlertStatus.RESOLVED, AlertStatus.DISMISSED},
    )


def expire_alert(db: Session, alert_id: UUID) -> Alert:
    return _transition(
        db,
        alert_id,
        to_status=AlertStatus.EXPIRED,
        event_type=AlertEventType.EXPIRED,
        allowed_from={AlertStatus.ACTIVE, AlertStatus.READ},
    )


def get_alert_summary(db: Session, *, user_id: UUID, family_id: UUID | None | object = _UNSET) -> AlertSummary:
    alerts = repository.list_alerts(db, user_id, family_id=family_id, limit=100)
    active_alerts = [alert for alert in alerts if alert.status == AlertStatus.ACTIVE]
    due_alerts = repository.list_due_alerts(db, user_id=user_id, family_id=family_id)
    return AlertSummary(
        user_id=str(user_id),
        count=len(alerts),
        active_count=len(active_alerts),
        due_count=len(due_alerts),
        latest_alert=_alert_dict(alerts[0]) if alerts else None,
        message="系统内暂无 active 提醒记录" if not active_alerts else "系统内存在 active 提醒记录",
    )


def _transition(
    db: Session,
    alert_id: UUID,
    *,
    to_status: AlertStatus,
    event_type: AlertEventType,
    allowed_from: set[AlertStatus],
    actor_user_id: UUID | None = None,
    note: str | None = None,
    resolved_at: datetime | None = None,
) -> Alert:
    alert = get_alert(db, alert_id)
    before = alert.status
    if before not in allowed_from:
        raise InvalidAlertTransitionError(f"cannot transition alert from {before.value} to {to_status.value}")
    updated = repository.update_alert_status(
        db,
        alert.id,
        to_status,
        resolved_at=resolved_at,
    )
    if updated is None:
        raise AlertNotFoundError("alert not found")
    repository.create_alert_event(
        db,
        alert_id=alert.id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        before_status=before,
        after_status=to_status,
        note=note,
    )
    return updated


def _alert_dict(alert: Alert) -> dict:
    return {
        "id": str(alert.id),
        "alert_type": alert.alert_type.value,
        "level": alert.level.value,
        "title": alert.title,
        "status": alert.status.value,
        "due_at": alert.due_at,
    }


def _validate_required_text(value: str | None, field_name: str) -> None:
    if not value or not value.strip():
        raise InvalidAlertError(f"{field_name} is required")


def _coerce_enum(enum_cls: type[StrEnum], value):
    if isinstance(value, enum_cls):
        return value
    return enum_cls(value)
