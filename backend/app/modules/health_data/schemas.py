from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MetricSummary:
    metric_type: str
    days: int
    count: int
    latest_value: float | str | None
    latest_measured_at: datetime | None
    min_value: float | None
    max_value: float | None
    avg_value: float | None
    unit: str | None
    data_quality: str
    records: list[dict]


@dataclass(frozen=True)
class BloodPressureSummary:
    days: int
    count: int
    latest_systolic: int | None
    latest_diastolic: int | None
    latest_pulse: int | None
    latest_measured_at: datetime | None
    avg_systolic: float | None
    avg_diastolic: float | None
    min_systolic: int | None
    max_systolic: int | None
    min_diastolic: int | None
    max_diastolic: int | None
    data_quality: str
    records: list[dict]
