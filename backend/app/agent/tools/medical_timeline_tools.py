from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.agent.schemas import AgentToolMetadata
from app.agent.tools.base import AgentTool
from app.modules.medical_timeline import service as medical_timeline_service


class MedicalFollowupsListTool(AgentTool):
    metadata = AgentToolMetadata(
        name="medical_timeline.followups.list",
        description="Read stored medical events that are marked as needing follow-up.",
        category="medical_timeline",
        access_mode="read",
        risk_level="medium",
        required_permission_type="medical_events",
        required_permission_action="view",
        requires_confirmation=False,
        input_schema_name="MedicalFollowupsListInput",
        output_schema_name="MedicalFollowupsListOutput",
        safety_notes=("Returns stored follow-up flags only; no treatment plan or medical conclusion.",),
    )

    def validate_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"limit": _bounded_int(payload.get("limit", 10), field_name="limit", minimum=1, maximum=50)}

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        db = _require_db(payload)
        events = medical_timeline_service.get_follow_up_events(
            db,
            user_id=payload["_target_user_id"],
            family_id=payload.get("_family_id"),
        )[: payload["limit"]]
        return {
            "status": "ok",
            "source": "system_records",
            "count": len(events),
            "items": [_event_summary(event) for event in events],
        }


def _event_summary(event) -> dict[str, Any]:
    return {
        "id": str(event.id),
        "event_type": getattr(event.event_type, "value", event.event_type),
        "title": event.title,
        "event_date": event.event_date,
        "follow_up_needed": bool(event.follow_up_needed),
        "follow_up_at": event.follow_up_at,
        "status": getattr(event.status, "value", event.status),
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
