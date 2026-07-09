from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class HealthQueryIntent(StrEnum):
    QUERY_METRICS = "query_metrics"
    QUERY_BLOOD_PRESSURE = "query_blood_pressure"
    QUERY_SYMPTOMS = "query_symptoms"
    QUERY_MEDICAL_EVENTS = "query_medical_events"
    QUERY_DOCUMENTS = "query_documents"
    QUERY_ALERTS = "query_alerts"
    QUERY_DAILY_STATUS = "query_daily_status"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class HealthQueryTimeRange:
    start_date: date
    end_date: date
    label: str
    days: int


@dataclass(frozen=True)
class HealthQueryPlan:
    intent: HealthQueryIntent
    time_range: HealthQueryTimeRange
    member_label: str | None = None
    member_scope: str = "self"
    metric_type: str | None = None
    source_type: str | None = None
    aggregation: str | None = None
    tool_name: str | None = None
    tool_input: dict | None = None
    safe_unknown_reason: str | None = None
    confidence: float | None = None
    needs_clarification: bool = False
    clarification_question: str | None = None
    planner_source: str = "rule"

    @property
    def is_unknown(self) -> bool:
        return self.intent == HealthQueryIntent.UNKNOWN
