from __future__ import annotations

from dataclasses import asdict
from typing import Any

from sqlalchemy.orm import Session

from app.api.sanitizers import sanitize_optional_json, sanitize_required_text
from app.agent.schemas import AgentToolMetadata
from app.agent.tools.base import AgentTool
from app.modules.health_record.enums import HealthRecordDraftType
from app.modules.health_record import service as health_record_service


class SymptomDraftCreateTool(AgentTool):
    metadata = AgentToolMetadata(
        name="health_record.symptom_draft.create",
        description="Create a pending symptom health-record draft from user-provided text.",
        category="health_record",
        access_mode="draft",
        risk_level="medium",
        required_permission_type="symptoms",
        required_permission_action="create",
        requires_confirmation=True,
        input_schema_name="SymptomDraftCreateInput",
        output_schema_name="SymptomDraftCreateOutput",
        safety_notes=(
            "Creates only a pending draft; does not create formal symptom_records.",
            "Does not infer causes, medical conclusions, prescription, dosage, or medication changes.",
        ),
    )

    def validate_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        raw_text = payload.get("raw_text", payload.get("symptom_text"))
        clean_text = sanitize_required_text(raw_text, max_length=2000)
        extracted_json = sanitize_optional_json(payload.get("extracted_json"), max_string_length=1000, max_total_length=5000)
        return {
            "raw_text": clean_text,
            "target_display_name": _optional_short_text(payload.get("target_display_name")),
            "extracted_json": _safe_symptom_draft_json(extracted_json),
            "missing_fields": _optional_string_list(payload.get("missing_fields")),
            "safety_flags": _optional_string_list(payload.get("safety_flags")),
        }

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        db = _require_db(payload)
        draft = health_record_service.create_health_record_draft(
            db,
            user_id=payload["_target_user_id"],
            family_id=payload.get("_family_id"),
            created_by_user_id=payload["_actor_user_id"],
            raw_text=payload["raw_text"],
            target_display_name=payload.get("target_display_name"),
            draft_type=HealthRecordDraftType.SYMPTOM,
            extracted_json=payload["extracted_json"],
            missing_fields=payload.get("missing_fields"),
            safety_flags=payload.get("safety_flags"),
        )
        return {
            "draft_id": str(draft.id),
            "status": getattr(draft.status, "value", draft.status),
            "safe_summary": "Pending symptom draft created from confirmed user input. It is not a formal health fact.",
        }


class SymptomsSummaryTool(AgentTool):
    metadata = AgentToolMetadata(
        name="health_record.symptoms.summary",
        description="Read a safe recent symptom-record summary for the target user.",
        category="health_record",
        access_mode="read",
        risk_level="medium",
        required_permission_type="symptoms",
        required_permission_action="view",
        requires_confirmation=False,
        input_schema_name="SymptomsSummaryInput",
        output_schema_name="SymptomsSummaryOutput",
        safety_notes=("Does not infer causes or diagnosis; recent items are limited and do not include raw_text.",),
    )

    def validate_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"days": _bounded_int(payload.get("days", 7), field_name="days", minimum=1, maximum=365)}

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        db = _require_db(payload)
        summary = health_record_service.get_symptom_summary(
            db,
            user_id=payload["_target_user_id"],
            family_id=payload.get("_family_id"),
            days=payload["days"],
        )
        data = asdict(summary)
        data["records"] = data["records"][:5]
        return {
            "status": "ok",
            "source": "system_records",
            "empty": summary.count == 0,
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


def _optional_short_text(value: Any) -> str | None:
    if value is None:
        return None
    from app.api.sanitizers import sanitize_optional_text

    return sanitize_optional_text(value, max_length=100)


def _optional_string_list(value: Any) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError("value must be a list")
    return [sanitize_required_text(item, max_length=120) for item in value]


def _safe_symptom_draft_json(value: Any) -> dict[str, Any]:
    if value is None:
        return {"source": "agent_tool"}
    if not isinstance(value, dict):
        raise ValueError("extracted_json must be a dict")
    value.setdefault("source", "agent_tool")
    return value
