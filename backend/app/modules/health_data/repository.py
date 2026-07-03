from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.health_data.enums import (
    BloodPressureArm,
    BloodPressureMeasurementContext,
    BloodPressurePosture,
    ConfidenceLevel,
    HealthDataImportStatus,
    HealthDataImportType,
    MetricSource,
    MetricType,
)
from app.modules.health_data.models import (
    BloodPressureRecord,
    HealthDataImportJob,
    HealthMetric,
)


def create_metric(
    db: Session,
    *,
    user_id: UUID,
    metric_type: MetricType,
    value_numeric: float | None = None,
    value_text: str | None = None,
    unit: str | None = None,
    measured_at: datetime,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
    source: MetricSource,
    source_detail: str | None = None,
    confidence_level: ConfidenceLevel,
    note: str | None = None,
) -> HealthMetric:
    metric = HealthMetric(
        user_id=user_id,
        metric_type=metric_type,
        value_numeric=value_numeric,
        value_text=value_text,
        unit=unit,
        measured_at=measured_at,
        period_start=period_start,
        period_end=period_end,
        source=source,
        source_detail=source_detail,
        confidence_level=confidence_level,
        note=note,
    )
    db.add(metric)
    db.flush()
    return metric


def list_metrics(
    db: Session,
    user_id: UUID,
    *,
    metric_type: MetricType | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    limit: int = 100,
) -> list[HealthMetric]:
    stmt = select(HealthMetric).where(HealthMetric.user_id == user_id)
    if metric_type is not None:
        stmt = stmt.where(HealthMetric.metric_type == metric_type)
    if start_at is not None:
        stmt = stmt.where(HealthMetric.measured_at >= start_at)
    if end_at is not None:
        stmt = stmt.where(HealthMetric.measured_at <= end_at)
    return list(
        db.scalars(stmt.order_by(HealthMetric.measured_at.desc()).limit(limit)),
    )


def list_recent_metrics(
    db: Session,
    user_id: UUID,
    *,
    metric_types: list[MetricType] | None = None,
    days: int = 7,
    limit_per_type: int = 20,
) -> list[HealthMetric]:
    start_at = datetime.now(timezone.utc) - timedelta(days=days)
    if not metric_types:
        return list_metrics(db, user_id, start_at=start_at, limit=limit_per_type)
    records: list[HealthMetric] = []
    for metric_type in metric_types:
        records.extend(
            list_metrics(
                db,
                user_id,
                metric_type=metric_type,
                start_at=start_at,
                limit=limit_per_type,
            ),
        )
    return records


def get_latest_metric(
    db: Session,
    user_id: UUID,
    metric_type: MetricType,
) -> HealthMetric | None:
    return db.scalar(
        select(HealthMetric)
        .where(HealthMetric.user_id == user_id, HealthMetric.metric_type == metric_type)
        .order_by(HealthMetric.measured_at.desc())
        .limit(1),
    )


def create_blood_pressure_record(
    db: Session,
    *,
    user_id: UUID,
    systolic: int,
    diastolic: int,
    pulse: int | None = None,
    measured_at: datetime,
    measurement_context: BloodPressureMeasurementContext,
    arm: BloodPressureArm,
    posture: BloodPressurePosture,
    source: MetricSource,
    confidence_level: ConfidenceLevel,
    note: str | None = None,
) -> BloodPressureRecord:
    record = BloodPressureRecord(
        user_id=user_id,
        systolic=systolic,
        diastolic=diastolic,
        pulse=pulse,
        measured_at=measured_at,
        measurement_context=measurement_context,
        arm=arm,
        posture=posture,
        source=source,
        confidence_level=confidence_level,
        note=note,
    )
    db.add(record)
    db.flush()
    return record


def list_blood_pressure_records(
    db: Session,
    user_id: UUID,
    *,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    limit: int = 100,
) -> list[BloodPressureRecord]:
    stmt = select(BloodPressureRecord).where(BloodPressureRecord.user_id == user_id)
    if start_at is not None:
        stmt = stmt.where(BloodPressureRecord.measured_at >= start_at)
    if end_at is not None:
        stmt = stmt.where(BloodPressureRecord.measured_at <= end_at)
    return list(
        db.scalars(stmt.order_by(BloodPressureRecord.measured_at.desc()).limit(limit)),
    )


def list_recent_blood_pressure(
    db: Session,
    user_id: UUID,
    *,
    days: int = 30,
    limit: int = 30,
) -> list[BloodPressureRecord]:
    start_at = datetime.now(timezone.utc) - timedelta(days=days)
    return list_blood_pressure_records(db, user_id, start_at=start_at, limit=limit)


def get_latest_blood_pressure(
    db: Session,
    user_id: UUID,
) -> BloodPressureRecord | None:
    return db.scalar(
        select(BloodPressureRecord)
        .where(BloodPressureRecord.user_id == user_id)
        .order_by(BloodPressureRecord.measured_at.desc())
        .limit(1),
    )


def create_import_job(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID | None = None,
    import_type: HealthDataImportType,
    source: MetricSource,
    file_name: str | None = None,
    file_path: str | None = None,
) -> HealthDataImportJob:
    job = HealthDataImportJob(
        user_id=user_id,
        family_id=family_id,
        import_type=import_type,
        source=source,
        file_name=file_name,
        file_path=file_path,
        status=HealthDataImportStatus.PENDING,
    )
    db.add(job)
    db.flush()
    return job


def update_import_job_status(
    db: Session,
    job_id: UUID,
    status: HealthDataImportStatus,
    *,
    total_count: int | None = None,
    success_count: int | None = None,
    failed_count: int | None = None,
    error_message: str | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
) -> HealthDataImportJob | None:
    job = get_import_job(db, job_id)
    if job is None:
        return None
    job.status = status
    if total_count is not None:
        job.total_count = total_count
    if success_count is not None:
        job.success_count = success_count
    if failed_count is not None:
        job.failed_count = failed_count
    if error_message is not None:
        job.error_message = error_message
    if started_at is not None:
        job.started_at = started_at
    if finished_at is not None:
        job.finished_at = finished_at
    db.flush()
    return job


def get_import_job(db: Session, job_id: UUID) -> HealthDataImportJob | None:
    return db.get(HealthDataImportJob, job_id)


def list_import_jobs(
    db: Session,
    user_id: UUID,
    *,
    status: HealthDataImportStatus | None = None,
    limit: int = 50,
) -> list[HealthDataImportJob]:
    stmt = select(HealthDataImportJob).where(HealthDataImportJob.user_id == user_id)
    if status is not None:
        stmt = stmt.where(HealthDataImportJob.status == status)
    return list(db.scalars(stmt.order_by(HealthDataImportJob.created_at.desc()).limit(limit)))
