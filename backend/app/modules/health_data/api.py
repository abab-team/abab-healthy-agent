from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id_for_demo, get_db
from app.modules.health_data import service
from app.modules.health_data.api_schemas import (
    BloodPressureCreateRequest,
    BloodPressureResponse,
    MetricCreateRequest,
    MetricResponse,
)
from app.modules.health_data.exceptions import (
    InvalidBloodPressureValueError,
    InvalidMetricValueError,
)
from app.modules.permissions import service as permission_service


router = APIRouter(tags=["health-data"])


@router.post(
    "/health-data/me/metrics",
    response_model=MetricResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_my_metric(
    payload: MetricCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    return _create_metric(db, user_id=current_user_id, payload=payload)


@router.get("/health-data/me/metrics/recent")
def get_my_recent_metrics(
    metric_types: list[str] | None = Query(default=None),
    days: int = Query(default=7, ge=1, le=365),
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    return {
        "items": [
            _metric_response(record)
            for record in _recent_metrics(
                db,
                user_id=current_user_id,
                metric_types=metric_types,
                days=days,
            )
        ]
    }


@router.get("/health-data/me/metrics/latest")
def get_my_latest_metrics(
    metric_types: list[str] | None = Query(default=None),
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    try:
        return service.get_latest_metrics_snapshot(
            db,
            user_id=current_user_id,
            metric_types=_parse_metric_types(metric_types),
        )
    except ValueError as exc:
        raise _bad_request(exc) from exc


@router.get("/health-data/me/metrics/{metric_type}/summary")
def get_my_metric_summary(
    metric_type: str,
    days: int = Query(default=7, ge=1, le=365),
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    return _metric_summary(db, user_id=current_user_id, metric_type=metric_type, days=days)


@router.post(
    "/health-data/me/blood-pressure",
    response_model=BloodPressureResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_my_blood_pressure(
    payload: BloodPressureCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    return _create_blood_pressure(db, user_id=current_user_id, payload=payload)


@router.get("/health-data/me/blood-pressure/recent")
def get_my_recent_blood_pressure(
    days: int = Query(default=30, ge=1, le=365),
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    return {
        "items": [
            _blood_pressure_response(record)
            for record in service.get_recent_blood_pressure(
                db,
                user_id=current_user_id,
                days=days,
            )
        ]
    }


@router.get("/health-data/me/blood-pressure/summary")
def get_my_blood_pressure_summary(
    days: int = Query(default=30, ge=1, le=365),
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    return service.get_blood_pressure_summary(db, user_id=current_user_id, days=days)


@router.get("/families/{family_id}/members/{target_user_id}/health-data/metrics/recent")
def get_family_member_recent_metrics(
    family_id: UUID,
    target_user_id: UUID,
    metric_types: list[str] | None = Query(default=None),
    days: int = Query(default=7, ge=1, le=365),
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "metrics", "view")
    return {
        "items": [
            _metric_response(record)
            for record in _recent_metrics(
                db,
                user_id=target_user_id,
                metric_types=metric_types,
                days=days,
            )
        ]
    }


@router.get("/families/{family_id}/members/{target_user_id}/health-data/metrics/{metric_type}/summary")
def get_family_member_metric_summary(
    family_id: UUID,
    target_user_id: UUID,
    metric_type: str,
    days: int = Query(default=7, ge=1, le=365),
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "metrics", "view")
    return _metric_summary(db, user_id=target_user_id, metric_type=metric_type, days=days)


@router.get("/families/{family_id}/members/{target_user_id}/health-data/blood-pressure/recent")
def get_family_member_recent_blood_pressure(
    family_id: UUID,
    target_user_id: UUID,
    days: int = Query(default=30, ge=1, le=365),
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "metrics", "view")
    return {
        "items": [
            _blood_pressure_response(record)
            for record in service.get_recent_blood_pressure(
                db,
                user_id=target_user_id,
                days=days,
            )
        ]
    }


@router.get("/families/{family_id}/members/{target_user_id}/health-data/blood-pressure/summary")
def get_family_member_blood_pressure_summary(
    family_id: UUID,
    target_user_id: UUID,
    days: int = Query(default=30, ge=1, le=365),
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "metrics", "view")
    return service.get_blood_pressure_summary(db, user_id=target_user_id, days=days)


@router.post(
    "/families/{family_id}/members/{target_user_id}/health-data/metrics",
    response_model=MetricResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_family_member_metric(
    family_id: UUID,
    target_user_id: UUID,
    payload: MetricCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "metrics", "create")
    return _create_metric(db, user_id=target_user_id, payload=payload)


@router.post(
    "/families/{family_id}/members/{target_user_id}/health-data/blood-pressure",
    response_model=BloodPressureResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_family_member_blood_pressure(
    family_id: UUID,
    target_user_id: UUID,
    payload: BloodPressureCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "metrics", "create")
    return _create_blood_pressure(db, user_id=target_user_id, payload=payload)


def _create_metric(db: Session, *, user_id: UUID, payload: MetricCreateRequest) -> dict:
    try:
        record = service.add_metric(
            db,
            user_id=user_id,
            metric_type=payload.metric_type,
            value_numeric=payload.value_numeric,
            value_text=payload.value_text,
            unit=payload.unit,
            measured_at=payload.measured_at,
            source=payload.source,
            confidence_level=payload.confidence_level,
            note=payload.note,
        )
    except (InvalidMetricValueError, ValueError) as exc:
        raise _bad_request(exc) from exc
    return _metric_response(record)


def _recent_metrics(
    db: Session,
    *,
    user_id: UUID,
    metric_types: list[str] | None,
    days: int,
):
    try:
        return service.get_recent_metrics(
            db,
            user_id=user_id,
            metric_types=_parse_metric_types(metric_types),
            days=days,
        )
    except ValueError as exc:
        raise _bad_request(exc) from exc


def _metric_summary(db: Session, *, user_id: UUID, metric_type: str, days: int):
    try:
        return service.get_metric_summary(
            db,
            user_id=user_id,
            metric_type=metric_type,
            days=days,
        )
    except ValueError as exc:
        raise _bad_request(exc) from exc


def _create_blood_pressure(
    db: Session,
    *,
    user_id: UUID,
    payload: BloodPressureCreateRequest,
) -> dict:
    try:
        record = service.add_blood_pressure_record(
            db,
            user_id=user_id,
            systolic=payload.systolic,
            diastolic=payload.diastolic,
            pulse=payload.pulse,
            measured_at=payload.measured_at,
            measurement_context=payload.measurement_context,
            arm=payload.arm,
            posture=payload.posture,
            source=payload.source,
            confidence_level=payload.confidence_level,
            note=payload.note,
        )
    except (InvalidBloodPressureValueError, ValueError) as exc:
        raise _bad_request(exc) from exc
    return _blood_pressure_response(record)


def _require_permission(
    db: Session,
    current_user_id: UUID,
    family_id: UUID,
    target_user_id: UUID,
    permission_type: str,
    action: str,
) -> None:
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


def _parse_metric_types(metric_types: list[str] | None) -> list[str] | None:
    if not metric_types:
        return None
    parsed: list[str] = []
    for value in metric_types:
        parsed.extend(part.strip() for part in value.split(",") if part.strip())
    return parsed or None


def _metric_response(record) -> dict:
    return {
        "id": record.id,
        "user_id": record.user_id,
        "metric_type": _enum_value(record.metric_type),
        "value_numeric": _float_or_none(record.value_numeric),
        "value_text": record.value_text,
        "unit": record.unit,
        "measured_at": record.measured_at,
        "source": _enum_value(record.source),
        "confidence_level": _enum_value(record.confidence_level),
        "note": record.note,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def _blood_pressure_response(record) -> dict:
    return {
        "id": record.id,
        "user_id": record.user_id,
        "systolic": record.systolic,
        "diastolic": record.diastolic,
        "pulse": record.pulse,
        "measured_at": record.measured_at,
        "measurement_context": _enum_value(record.measurement_context),
        "arm": _enum_value(record.arm),
        "posture": _enum_value(record.posture),
        "source": _enum_value(record.source),
        "confidence_level": _enum_value(record.confidence_level),
        "note": record.note,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def _enum_value(value):
    return value.value if hasattr(value, "value") else value


def _float_or_none(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return value


def _bad_request(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
