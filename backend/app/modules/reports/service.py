from __future__ import annotations

from datetime import date, timedelta
from enum import StrEnum
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.reports import repository
from app.modules.reports.enums import (
    DailyReportGeneratedBy,
    DailyReportGenerationStatus,
    DailyReportStatusLevel,
)
from app.modules.reports.exceptions import InvalidDailyReportError
from app.modules.reports.models import DailyReport
from app.modules.reports.schemas import DailyReportSnapshot


_UNSET = repository._UNSET


def save_daily_report(
    db: Session,
    *,
    user_id: UUID,
    report_date: date,
    status_level: DailyReportStatusLevel | str,
    summary_text: str | None = None,
    family_id: UUID | None = None,
    overall_status: str | None = None,
    highlights: list[dict] | None = None,
    concerns: list[dict] | None = None,
    suggestions: list[dict] | None = None,
    metrics_snapshot: dict | None = None,
    related_symptom_record_ids: list[str] | None = None,
    related_alert_ids: list[str] | None = None,
    generated_by: DailyReportGeneratedBy | str = DailyReportGeneratedBy.SYSTEM,
    generation_status: DailyReportGenerationStatus | str = DailyReportGenerationStatus.SUCCESS,
) -> DailyReport:
    if report_date is None:
        raise InvalidDailyReportError("report_date is required")
    return repository.upsert_daily_report(
        db,
        user_id,
        report_date,
        family_id=family_id,
        overall_status=overall_status,
        status_level=_coerce_enum(DailyReportStatusLevel, status_level),
        summary_text=summary_text,
        highlights=highlights,
        concerns=concerns,
        suggestions=suggestions,
        metrics_snapshot=metrics_snapshot,
        related_symptom_record_ids=related_symptom_record_ids,
        related_alert_ids=related_alert_ids,
        generated_by=_coerce_enum(DailyReportGeneratedBy, generated_by),
        generation_status=_coerce_enum(DailyReportGenerationStatus, generation_status),
    )


def get_daily_report(
    db: Session,
    *,
    user_id: UUID,
    report_date: date,
    family_id: UUID | None | object = _UNSET,
) -> DailyReport | None:
    return repository.get_daily_report(db, user_id, report_date, family_id=family_id)


def get_latest_daily_report(db: Session, *, user_id: UUID, family_id: UUID | None | object = _UNSET) -> DailyReport | None:
    return repository.get_latest_daily_report(db, user_id, family_id=family_id)


def list_recent_daily_reports(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID | None | object = _UNSET,
    days: int = 30,
) -> list[DailyReport]:
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    return repository.list_daily_reports(db, user_id, family_id=family_id, start_date=start_date, end_date=end_date, limit=days)


def mark_daily_report_failed(
    db: Session,
    *,
    user_id: UUID,
    report_date: date,
) -> DailyReport:
    report = repository.update_generation_status(
        db,
        user_id,
        report_date,
        DailyReportGenerationStatus.FAILED,
    )
    if report is None:
        report = save_daily_report(
            db,
            user_id=user_id,
            report_date=report_date,
            status_level=DailyReportStatusLevel.INSUFFICIENT_DATA,
            generation_status=DailyReportGenerationStatus.FAILED,
        )
    return report


def get_daily_report_snapshot(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID | None | object = _UNSET,
) -> DailyReportSnapshot:
    report = get_latest_daily_report(db, user_id=user_id, family_id=family_id)
    if report is None:
        return DailyReportSnapshot(
            user_id=str(user_id),
            has_report=False,
            message="系统内暂无日报记录",
            report_date=None,
            status_level=None,
            summary_text=None,
            generation_status=None,
        )
    return DailyReportSnapshot(
        user_id=str(user_id),
        has_report=True,
        message="系统内存在日报记录",
        report_date=report.report_date,
        status_level=report.status_level.value,
        summary_text=report.summary_text,
        generation_status=report.generation_status.value,
    )


def _coerce_enum(enum_cls: type[StrEnum], value):
    if isinstance(value, enum_cls):
        return value
    return enum_cls(value)
