from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id_for_demo, get_db
from app.modules.permissions import service as permission_service
from app.modules.reports import service
from app.modules.reports.api_schemas import DailyReportResponse, DailyReportSaveRequest
from app.modules.reports.exceptions import InvalidDailyReportError


router = APIRouter(tags=["reports"])


@router.post("/reports/me/daily", response_model=DailyReportResponse, status_code=status.HTTP_201_CREATED)
def save_my_daily_report(payload: DailyReportSaveRequest, current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    return _save_daily_report(db, user_id=current_user_id, family_id=None, payload=payload)


@router.get("/reports/me/daily/latest")
def get_my_latest_daily_report(current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    report = service.get_latest_daily_report(db, user_id=current_user_id)
    if report is None:
        return service.get_daily_report_snapshot(db, user_id=current_user_id)
    return _report_response(report)


@router.get("/reports/me/daily/recent")
def list_my_recent_daily_reports(days: int = Query(default=30, ge=1, le=365), current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    return {"items": [_report_response(report) for report in service.list_recent_daily_reports(db, user_id=current_user_id, days=days)]}


@router.get("/reports/me/daily/{report_date}", response_model=DailyReportResponse)
def get_my_daily_report(report_date: date, current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    report = service.get_daily_report(db, user_id=current_user_id, report_date=report_date)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="daily report not found")
    return _report_response(report)


@router.post("/reports/me/daily/{report_date}/mark-failed", response_model=DailyReportResponse)
def mark_my_daily_report_failed(report_date: date, current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    return _report_response(service.mark_daily_report_failed(db, user_id=current_user_id, report_date=report_date))


@router.get("/families/{family_id}/members/{target_user_id}/reports/daily/latest")
def get_family_member_latest_daily_report(family_id: UUID, target_user_id: UUID, current_user_id: UUID = Depends(get_current_user_id_for_demo), db: Session = Depends(get_db)):
    _require_permission(db, current_user_id, family_id, target_user_id, "reports", "view")
    report = service.get_latest_daily_report(db, user_id=target_user_id, family_id=family_id)
    if report is None:
        return service.get_daily_report_snapshot(db, user_id=target_user_id, family_id=family_id)
    return _report_response(report)


@router.get("/families/{family_id}/members/{target_user_id}/reports/daily/recent")
def list_family_member_recent_daily_reports(
    family_id: UUID,
    target_user_id: UUID,
    days: int = Query(default=30, ge=1, le=365),
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "reports", "view")
    return {"items": [_report_response(report) for report in service.list_recent_daily_reports(db, user_id=target_user_id, family_id=family_id, days=days)]}


@router.post("/families/{family_id}/members/{target_user_id}/reports/daily", response_model=DailyReportResponse, status_code=status.HTTP_201_CREATED)
def save_family_member_daily_report(
    family_id: UUID,
    target_user_id: UUID,
    payload: DailyReportSaveRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "reports", "generate")
    return _save_daily_report(db, user_id=target_user_id, family_id=family_id, payload=payload)


def _save_daily_report(db: Session, *, user_id: UUID, family_id: UUID | None, payload: DailyReportSaveRequest) -> dict:
    try:
        report = service.save_daily_report(db, user_id=user_id, family_id=family_id, **payload.model_dump())
    except (InvalidDailyReportError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _report_response(report)


def _require_permission(db: Session, current_user_id: UUID, family_id: UUID, target_user_id: UUID, permission_type: str, action: str) -> None:
    result = permission_service.check_member_permission(
        db,
        current_user_id=current_user_id,
        family_id=family_id,
        target_user_id=target_user_id,
        permission_type=permission_type,
        action=action,
    )
    if not result.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result.safe_message)


def _report_response(report) -> dict:
    return {
        "id": report.id,
        "user_id": report.user_id,
        "family_id": report.family_id,
        "report_date": report.report_date,
        "overall_status": report.overall_status,
        "status_level": _enum_value(report.status_level),
        "summary_text": report.summary_text,
        "highlights": report.highlights,
        "concerns": report.concerns,
        "suggestions": report.suggestions,
        "metrics_snapshot": report.metrics_snapshot,
        "related_symptom_record_ids": report.related_symptom_record_ids,
        "related_alert_ids": report.related_alert_ids,
        "generated_by": _enum_value(report.generated_by),
        "generation_status": _enum_value(report.generation_status),
        "created_at": report.created_at,
        "updated_at": report.updated_at,
    }


def _enum_value(value):
    return value.value if hasattr(value, "value") else value
