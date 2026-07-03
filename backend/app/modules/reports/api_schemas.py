from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.reports.enums import (
    DailyReportGeneratedBy,
    DailyReportGenerationStatus,
    DailyReportStatusLevel,
)


class DailyReportSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_date: date
    status_level: DailyReportStatusLevel
    summary_text: str | None = None
    overall_status: str | None = None
    highlights: list[dict] | None = None
    concerns: list[dict] | None = None
    suggestions: list[dict] | None = None
    metrics_snapshot: dict | None = None
    related_symptom_record_ids: list[str] | None = None
    related_alert_ids: list[str] | None = None
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
