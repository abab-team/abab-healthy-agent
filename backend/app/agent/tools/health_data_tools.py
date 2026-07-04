from __future__ import annotations

from dataclasses import asdict
from typing import Any

from sqlalchemy.orm import Session

from app.agent.schemas import AgentToolMetadata
from app.agent.tools.base import AgentTool
from app.modules.health_data import service as health_data_service


class BloodPressureSummaryTool(AgentTool):
    metadata = AgentToolMetadata(
        name="health_data.blood_pressure.summary",
        description="Read a stored blood pressure summary for the target user.",
        category="health_data",
        access_mode="read",
        risk_level="low",
        required_permission_type="metrics",
        required_permission_action="view",
        requires_confirmation=False,
        input_schema_name="BloodPressureSummaryInput",
        output_schema_name="BloodPressureSummaryOutput",
        safety_notes=("Returns aggregate stored values only; no normal/abnormal judgment or medication advice.",),
    )

    def validate_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"days": _bounded_int(payload.get("days", 7), field_name="days", minimum=1, maximum=365)}

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        db = _require_db(payload)
        summary = health_data_service.get_blood_pressure_summary(
            db,
            user_id=payload["_target_user_id"],
            days=payload["days"],
        )
        data = asdict(summary)
        data["records"] = data["records"][:5]
        return {
            "status": "ok",
            "source": "system_records",
            "empty": summary.count == 0,
            "no_records_message": "No blood pressure records were found in system records for this period." if summary.count == 0 else None,
            "summary": data,
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
