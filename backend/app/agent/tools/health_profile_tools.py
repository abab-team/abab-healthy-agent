from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.agent.schemas import AgentToolMetadata
from app.agent.tools.base import AgentTool
from app.modules.health_profile import service as health_profile_service


class HealthProfileGetTool(AgentTool):
    metadata = AgentToolMetadata(
        name="health_profile.get",
        description="Read a safe health profile summary for the target user.",
        category="health_profile",
        access_mode="read",
        risk_level="low",
        required_permission_type="health_profile",
        required_permission_action="view",
        requires_confirmation=False,
        input_schema_name="HealthProfileGetInput",
        output_schema_name="HealthProfileGetOutput",
        safety_notes=("Returns only stored profile fields and does not generate medical judgment.",),
    )

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        db = _require_db(payload)
        target_user_id = payload["_target_user_id"]
        profile = health_profile_service.get_profile(db, target_user_id)
        if profile is None:
            return {
                "status": "ok",
                "source": "system_records",
                "empty": True,
                "profile": None,
            }
        birth_year = profile.birth_date.year if profile.birth_date else None
        return {
            "status": "ok",
            "source": "system_records",
            "empty": False,
            "profile": {
                "user_id": str(profile.user_id),
                "birth_year": birth_year,
                "age_range": _age_range(profile.birth_date),
                "gender": _enum_value(profile.gender),
                "blood_type": _enum_value(profile.blood_type),
                "height_cm": float(profile.height_cm) if profile.height_cm is not None else None,
                "health_goal": profile.health_goal,
                "allergies": profile.allergy_summary,
                "chronic_conditions": profile.chronic_conditions_summary,
                "medication_summary": profile.medication_summary,
            },
        }


def _age_range(birth_date: date | None) -> str | None:
    if birth_date is None:
        return None
    age = max(0, date.today().year - birth_date.year)
    bucket_start = age // 10 * 10
    return f"{bucket_start}-{bucket_start + 9}"


def _enum_value(value: Any) -> str | None:
    return getattr(value, "value", value) if value is not None else None


def _require_db(payload: dict[str, Any]) -> Session:
    db = payload.get("_db")
    if not isinstance(db, Session):
        raise ValueError("tool execution context is missing database session")
    return db
