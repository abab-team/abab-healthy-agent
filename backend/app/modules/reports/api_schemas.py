from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.api.validators import JsonDict, JsonList, STRICT_MODEL_CONFIG, StringList, SummaryText
from app.modules.reports.enums import (
    DailyReportGeneratedBy,
    DailyReportGenerationStatus,
    DailyReportStatusLevel,
)


class DailyReportSaveRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    report_date: date
    status_level: DailyReportStatusLevel
    summary_text: SummaryText = None
    overall_status: SummaryText = None
    highlights: JsonList = None
    concerns: JsonList = None
    suggestions: JsonList = None
    metrics_snapshot: JsonDict = None
    related_symptom_record_ids: StringList = None
    related_alert_ids: StringList = None
    generated_by: DailyReportGeneratedBy = DailyReportGeneratedBy.SYSTEM
    generation_status: DailyReportGenerationStatus = DailyReportGenerationStatus.SUCCESS


class DailyReportResponse(BaseModel):
    id: UUID
    user_id: UUID
    family_id: UUID | None = None
    report_date: date
    overall_status: str | None = None
    status_level: str
    summary_text: str | None = None
    highlights: list[dict] | None = None
    concerns: list[dict] | None = None
    suggestions: list[dict] | None = None
    metrics_snapshot: dict | None = None
    related_symptom_record_ids: list[str] | None = None
    related_alert_ids: list[str] | None = None
    generated_by: str
    generation_status: str
    created_at: datetime
    updated_at: datetime
