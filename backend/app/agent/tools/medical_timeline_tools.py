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


class MedicalEventsQueryTool(AgentTool):
    metadata = AgentToolMetadata(
        name="medical_timeline.events.query",
        description="Read stored medical timeline event summaries for the target user.",
        category="medical_timeline",
        access_mode="read",
        risk_level="medium",
        required_permission_type="medical_events",
        required_permission_action="view",
        requires_confirmation=False,
        input_schema_name="MedicalEventsQueryInput",
        output_schema_name="MedicalEventsQueryOutput",
        safety_notes=("Returns stored event metadata only; no treatment advice or medical conclusion.",),
    )

    def validate_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"days": _bounded_int(payload.get("days", 365), field_name="days", minimum=1, maximum=365)}

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        db = _require_db(payload)
        summary = medical_timeline_service.get_medical_event_summary(
            db,
            user_id=payload["_target_user_id"],
            family_id=payload.get("_family_id"),
            days=payload["days"],
        )
        return {
            "status": "ok",
            "source": "system_records",
            "empty": summary.count == 0,
            "count": summary.count,
            "follow_up_needed_count": summary.follow_up_needed_count,
            "coverage_note": f"Based only on {summary.count} system medical timeline records.",
            "latest_event": summary.latest_event,
            "items": summary.events[:10],
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
