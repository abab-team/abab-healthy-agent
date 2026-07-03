from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.health_data.enums import (
    BloodPressureArm,
    BloodPressureMeasurementContext,
    BloodPressurePosture,
    ConfidenceLevel,
    MetricSource,
    MetricType,
)


class MetricCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_type: MetricType | str
    value_numeric: float | None = None
    value_text: str | None = Field(default=None, max_length=255)
    unit: str | None = Field(default=None, max_length=32)
    measured_at: datetime | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    source: MetricSource = MetricSource.MANUAL
    source_detail: str | None = Field(default=None, max_length=255)
    confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH
    note: str | None = None

    @model_validator(mode="after")
    def validate_value(self) -> MetricCreateRequest:
        if self.value_numeric is None and self.value_text is None:
            raise ValueError("value_numeric or value_text is required")
        if str(self.metric_type) in {"blood_pressure", "blood-pressure"}:
            raise ValueError("blood pressure must use the blood-pressure endpoint")
        return self


class MetricResponse(BaseModel):
    id: UUID
    user_id: UUID
    metric_type: str
    value_numeric: float | None = None
    value_text: str | None = None
    unit: str | None = None
    measured_at: datetime
    source: str
    confidence_level: str
    note: str | None = None
    created_at: datetime
    updated_at: datetime


class BloodPressureCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    systolic: int
    diastolic: int
    pulse: int | None = None
    measured_at: datetime | None = None
    measurement_context: BloodPressureMeasurementContext = BloodPressureMeasurementContext.UNKNOWN
    arm: BloodPressureArm = BloodPressureArm.UNKNOWN
    posture: BloodPressurePosture = BloodPressurePosture.UNKNOWN
    source: MetricSource = MetricSource.MANUAL
    confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH
    note: str | None = None


class BloodPressureResponse(BaseModel):
    id: UUID
    user_id: UUID
    systolic: int
    diastolic: int
    pulse: int | None = None
    measured_at: datetime
    measurement_context: str
    arm: str
    posture: str
    source: str
    confidence_level: str
    note: str | None = None
    created_at: datetime
    updated_at: datetime
