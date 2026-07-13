from __future__ import annotations

from dataclasses import asdict
from typing import Any

from sqlalchemy.orm import Session

from app.agent.schemas import AgentToolMetadata
from app.agent.tools.base import AgentTool
from app.modules.health_data import service as health_data_service
from app.modules.health_data.metric_types import get_metric_definition


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


class MetricSummaryTool(AgentTool):
    metadata = AgentToolMetadata(
        name="health_data.metric.summary",
        description="Read a stored metric summary for the target user.",
        category="health_data",
        access_mode="read",
        risk_level="low",
        required_permission_type="metrics",
        required_permission_action="view",
        requires_confirmation=False,
        input_schema_name="MetricSummaryInput",
        output_schema_name="MetricSummaryOutput",
        safety_notes=("Returns aggregate stored values only; no medical judgment.",),
    )

    def validate_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        metric_type = str(payload.get("metric_type") or "").strip()
        if not metric_type:
            raise ValueError("metric_type is required")
        return {
            "metric_type": metric_type,
            "days": _bounded_int(payload.get("days", 7), field_name="days", minimum=1, maximum=365),
            "aggregation": str(payload.get("aggregation") or "summary")[:32],
        }

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        db = _require_db(payload)
        summary = health_data_service.get_metric_summary(
            db,
            user_id=payload["_target_user_id"],
            metric_type=payload["metric_type"],
            days=payload["days"],
        )
        data = asdict(summary)
        data["records"] = data["records"][:10]
        definition = get_metric_definition(summary.metric_type)
        return {
            "status": "ok",
            "source": "system_records",
            "empty": summary.count == 0,
            "aggregation": payload["aggregation"],
            "coverage_note": f"Based only on {summary.count} system records in the selected period.",
            "metric_definition": {
                "label": definition.label,
                "default_unit": definition.default_unit,
            } if definition else None,
            "summary": data,
        }


class RecentMetricsTool(AgentTool):
    metadata = AgentToolMetadata(
        name="health_data.metrics.recent",
        description="Read recent metric records for the target user.",
        category="health_data",
        access_mode="read",
        risk_level="low",
        required_permission_type="metrics",
        required_permission_action="view",
        requires_confirmation=False,
        input_schema_name="RecentMetricsInput",
        output_schema_name="RecentMetricsOutput",
        safety_notes=("Returns recent stored metric records without interpretation.",),
    )

    def validate_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        metric_type = payload.get("metric_type")
        return {
            "metric_type": str(metric_type).strip() if metric_type else None,
            "days": _bounded_int(payload.get("days", 7), field_name="days", minimum=1, maximum=365),
            "limit": _bounded_int(payload.get("limit", 10), field_name="limit", minimum=1, maximum=50),
        }

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        db = _require_db(payload)
        metric_types = [payload["metric_type"]] if payload.get("metric_type") else None
        records = health_data_service.get_recent_metrics(
            db,
            user_id=payload["_target_user_id"],
            metric_types=metric_types,
            days=payload["days"],
        )[: payload["limit"]]
        metric_summaries = health_data_service.get_recent_metric_overview(
            db,
            user_id=payload["_target_user_id"],
            days=payload["days"],
        )
        return {
            "status": "ok",
            "source": "system_records",
            "empty": len(records) == 0,
            "count": len(records),
            "coverage_note": f"Based only on system records in the last {payload['days']} days.",
            "items": [_metric_record_summary(record) for record in records],
            "metric_summaries": metric_summaries,
        }


def _metric_record_summary(record) -> dict[str, Any]:
    return {
        "id": str(record.id),
        "metric_type": getattr(record.metric_type, "value", record.metric_type),
        "value_numeric": record.value_numeric,
        "value_text": record.value_text,
        "unit": record.unit,
        "measured_at": record.measured_at,
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
