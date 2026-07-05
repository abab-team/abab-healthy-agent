from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.api.sanitizers import sanitize_optional_text, sanitize_required_text
from app.agent import safety
from app.agent.schemas import AgentToolMetadata
from app.agent.tools.base import AgentTool
from app.modules.alerts.enums import AlertLevel, AlertSource, AlertType
from app.modules.alerts import service as alert_service


class AlertCreateTool(AgentTool):
    metadata = AgentToolMetadata(
        name="alerts.create",
        description="Create a confirmed health reminder alert without making medical judgments.",
        category="alert",
        access_mode="write",
        risk_level="medium",
        required_permission_type="alerts",
        required_permission_action="create",
        requires_confirmation=True,
        input_schema_name="AlertCreateInput",
        output_schema_name="AlertCreateOutput",
        safety_notes=(
            "Creates reminders only; does not create diagnosis, treatment plan, prescription, dosage, or medication-change advice.",
            "Until a dedicated alerts:create permission exists, the executor checks alerts:view plus family membership.",
        ),
    )

    def validate_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        alert_type = sanitize_optional_text(payload.get("alert_type"), max_length=64) or AlertType.MEDICAL_FOLLOW_UP.value
        level = sanitize_optional_text(payload.get("level"), max_length=32) or AlertLevel.INFO.value
        title = sanitize_required_text(payload.get("title"), max_length=120)
        message = sanitize_required_text(payload.get("message"), max_length=1000)
        suggested_action = sanitize_optional_text(payload.get("suggested_action"), max_length=1000)
        trigger_reason = sanitize_optional_text(payload.get("trigger_reason"), max_length=1000)
        _reject_unsafe_reminder_text(title, message, suggested_action, trigger_reason)
        return {
            "alert_type": alert_type,
            "level": level,
            "title": title,
            "message": message,
            "suggested_action": suggested_action,
            "trigger_reason": trigger_reason,
            "related_entity_type": sanitize_optional_text(payload.get("related_entity_type"), max_length=120),
            "related_entity_id": _optional_uuid(payload.get("related_entity_id")),
            "due_at": _optional_datetime(payload.get("due_at")),
        }

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        db = _require_db(payload)
        alert = alert_service.create_alert(
            db,
            user_id=payload["_target_user_id"],
            family_id=payload.get("_family_id"),
            created_by_user_id=payload["_actor_user_id"],
            alert_type=payload["alert_type"],
            level=payload["level"],
            title=payload["title"],
            message=payload["message"],
            suggested_action=payload.get("suggested_action"),
            related_entity_type=payload.get("related_entity_type"),
            related_entity_id=payload.get("related_entity_id"),
            trigger_reason=payload.get("trigger_reason"),
            due_at=payload.get("due_at"),
            source=AlertSource.AGENT,
        )
        return {
            "alert_id": str(alert.id),
            "status": getattr(alert.status, "value", alert.status),
            "safe_summary": "Reminder alert created from confirmed user input. It is for scheduling or record keeping only.",
        }


class ActiveAlertsListTool(AgentTool):
    metadata = AgentToolMetadata(
        name="alerts.active.list",
        description="Read active alert summaries for the target user.",
        category="alert",
        access_mode="read",
        risk_level="low",
        required_permission_type="alerts",
        required_permission_action="view",
        requires_confirmation=False,
        input_schema_name="ActiveAlertsListInput",
        output_schema_name="ActiveAlertsListOutput",
        safety_notes=("Alerts are reminders from system records and are not diagnosis.",),
    )

    def validate_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"limit": _bounded_int(payload.get("limit", 10), field_name="limit", minimum=1, maximum=50)}

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        db = _require_db(payload)
        alerts = alert_service.get_active_alerts(
            db,
            user_id=payload["_target_user_id"],
            family_id=payload.get("_family_id"),
        )[: payload["limit"]]
        return {
            "status": "ok",
            "source": "system_records",
            "empty": len(alerts) == 0,
            "no_records_message": "No active alerts were found in system records." if not alerts else None,
            "count": len(alerts),
            "items": [_alert_summary(alert) for alert in alerts],
        }


def _alert_summary(alert) -> dict[str, Any]:
    return {
        "id": str(alert.id),
        "alert_type": getattr(alert.alert_type, "value", alert.alert_type),
        "level": getattr(alert.level, "value", alert.level),
        "title": alert.title,
        "status": getattr(alert.status, "value", alert.status),
        "due_at": alert.due_at,
    }


def _bounded_int(value: Any, *, field_name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if number < minimum or number > maximum:
        raise ValueError(f"{field_name} must be between {minimum} and {maximum}")
    return number


def _require_db(payload: dict[str, Any]) -> Session:
    db = payload.get("_db")
    if not isinstance(db, Session):
        raise ValueError("tool execution context is missing database session")
    return db


def _reject_unsafe_reminder_text(*values: str | None) -> None:
    policy = safety.AgentSafetyPolicy()
    for value in values:
        if not value:
            continue
        decision = policy.evaluate_output(value)
        if decision.blocked:
            raise ValueError("reminder text contains unsafe medical advice")


def _optional_uuid(value: Any):
    if value is None or value == "":
        return None
    from uuid import UUID

    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _optional_datetime(value: Any):
    if value is None or value == "":
        return None
    from datetime import datetime

    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise ValueError("due_at must be an ISO datetime")
