from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.api.validators import Note, STRICT_MODEL_CONFIG, ShortText, SourceDetail
from app.modules.health_data.enums import (
    BloodPressureArm,
    BloodPressureMeasurementContext,
    BloodPressurePosture,
    ConfidenceLevel,
    HealthDataImportType,
    MetricSource,
    MetricType,
)


class MetricCreateRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    metric_type: MetricType | str
    value_numeric: float | None = Field(default=None, ge=0, le=1_000_000)
    value_text: ShortText = None
    unit: ShortText = None
    measured_at: datetime | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    source: MetricSource = MetricSource.MANUAL
    source_detail: SourceDetail = None
    confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH
    note: Note = None

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
    model_config = STRICT_MODEL_CONFIG

    systolic: int = Field(gt=0, le=400)
    diastolic: int = Field(gt=0, le=300)
    pulse: int | None = Field(default=None, gt=0, le=300)
    measured_at: datetime | None = None
    measurement_context: BloodPressureMeasurementContext = BloodPressureMeasurementContext.UNKNOWN
    arm: BloodPressureArm = BloodPressureArm.UNKNOWN
    posture: BloodPressurePosture = BloodPressurePosture.UNKNOWN
    source: MetricSource = MetricSource.MANUAL
    confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH
    note: Note = None


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


class TrendSeriesResponse(BaseModel):
    metric_type: str
    label: str
    unit: str | None = None
    count: int
    points: list[dict]
    summary: str
    data_quality: str


class ArchiveTrendsResponse(BaseModel):
    days: int
    generated_from: str
    disclaimer: str
    series: list[TrendSeriesResponse]


class ImportPreviewRow(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    metric_type: MetricType | str
    measured_at: datetime
    value_numeric: float | None = Field(default=None, ge=0, le=1_000_000)
    unit: str | None = Field(default=None, max_length=32)
    systolic: int | None = Field(default=None, gt=0, le=400)
    diastolic: int | None = Field(default=None, gt=0, le=300)
    pulse: int | None = Field(default=None, gt=0, le=300)
    note: Note = None


class ImportPreviewRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    import_type: HealthDataImportType = HealthDataImportType.CSV
    file_name: str | None = Field(default=None, max_length=255)
    rows: list[ImportPreviewRow] = Field(default_factory=list, min_length=1, max_length=200)


class ImportPreviewResponse(BaseModel):
    import_type: str
    file_name: str | None = None
    total_count: int
    valid_count: int
    invalid_count: int
    preview_rows: list[dict]
    errors: list[dict]
    will_write: bool
    disclaimer: str


class ImportConfirmRequest(ImportPreviewRequest):
    confirmation: bool


class ImportConfirmResponse(ImportPreviewResponse):
    job_id: UUID | None = None
    status: str
    created_records_count: int
