from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.reports.enums import (
    DailyReportGeneratedBy,
    DailyReportGenerationStatus,
    DailyReportStatusLevel,
)
from app.modules.reports.models import DailyReport


_UNSET = object()


def create_daily_report(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID | None = None,
    report_date: date,
    overall_status: str | None = None,
    status_level: DailyReportStatusLevel,
    summary_text: str | None = None,
    highlights: list[dict] | None = None,
    concerns: list[dict] | None = None,
    suggestions: list[dict] | None = None,
    metrics_snapshot: dict | None = None,
    related_symptom_record_ids: list[str] | None = None,
    related_alert_ids: list[str] | None = None,
    generated_by: DailyReportGeneratedBy = DailyReportGeneratedBy.SYSTEM,
    generation_status: DailyReportGenerationStatus = DailyReportGenerationStatus.SUCCESS,
) -> DailyReport:
    report = DailyReport(
        user_id=user_id,
        family_id=family_id,
        report_date=report_date,
        overall_status=overall_status,
        status_level=status_level,
        summary_text=summary_text,
        highlights=highlights,
        concerns=concerns,
        suggestions=suggestions,
        metrics_snapshot=metrics_snapshot,
        related_symptom_record_ids=related_symptom_record_ids,
        related_alert_ids=related_alert_ids,
        generated_by=generated_by,
        generation_status=generation_status,
    )
    db.add(report)
    db.flush()
    return report


def get_daily_report(
    db: Session,
    user_id: UUID,
    report_date: date,
    *,
    family_id: UUID | None | object = _UNSET,
) -> DailyReport | None:
    stmt = select(DailyReport).where(
        DailyReport.user_id == user_id,
        DailyReport.report_date == report_date,
    )
    if family_id is not _UNSET:
        stmt = stmt.where(DailyReport.family_id == family_id)
    return db.scalar(stmt)


def get_latest_daily_report(db: Session, user_id: UUID, *, family_id: UUID | None | object = _UNSET) -> DailyReport | None:
    stmt = (
        select(DailyReport)
        .where(DailyReport.user_id == user_id)
        .order_by(DailyReport.report_date.desc(), DailyReport.created_at.desc())
        .limit(1)
    )
    if family_id is not _UNSET:
        stmt = stmt.where(DailyReport.family_id == family_id)
    return db.scalar(stmt)


def list_daily_reports(
    db: Session,
    user_id: UUID,
    *,
    family_id: UUID | None | object = _UNSET,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 30,
) -> list[DailyReport]:
    stmt = select(DailyReport).where(DailyReport.user_id == user_id)
    if family_id is not _UNSET:
        stmt = stmt.where(DailyReport.family_id == family_id)
    if start_date is not None:
        stmt = stmt.where(DailyReport.report_date >= start_date)
    if end_date is not None:
        stmt = stmt.where(DailyReport.report_date <= end_date)
    return list(db.scalars(stmt.order_by(DailyReport.report_date.desc()).limit(limit)))


def upsert_daily_report(
    db: Session,
    user_id: UUID,
    report_date: date,
    *,
    family_id: UUID | None = None,
    **fields,
) -> DailyReport:
    report = get_daily_report(db, user_id, report_date, family_id=family_id)
    if report is None:
        return create_daily_report(
            db,
            user_id=user_id,
            family_id=family_id,
            report_date=report_date,
            **fields,
        )
    for key, value in fields.items():
        setattr(report, key, value)
    db.flush()
    return report


def update_generation_status(
    db: Session,
    user_id: UUID,
    report_date: date,
    generation_status: DailyReportGenerationStatus,
) -> DailyReport | None:
    report = get_daily_report(db, user_id, report_date)
    if report is None:
        return None
    report.generation_status = generation_status
    db.flush()
    return report
