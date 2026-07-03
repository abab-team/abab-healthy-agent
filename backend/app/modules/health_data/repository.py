# 模块领域：健康指标模块
# 领域说明：负责血压、体重、睡眠、活动等可量化指标的录入、查询和统计。
# 文件职责：仓储文件。封装数据库查询和写入细节，让业务服务只表达业务意图。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

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


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
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
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
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


# 函数职责：列表查询流程，按过滤条件返回一组对象，并保持排序、分页或范围语义稳定。
# 业务边界：返回集合时要避免把未授权数据暴露给调用方。
def list_metrics(
    db: Session,
    user_id: UUID,
    *,
    metric_type: MetricType | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    limit: int = 100,
) -> list[HealthMetric]:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    stmt = select(HealthMetric).where(HealthMetric.user_id == user_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if metric_type is not None:
        stmt = stmt.where(HealthMetric.metric_type == metric_type)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if start_at is not None:
        stmt = stmt.where(HealthMetric.measured_at >= start_at)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if end_at is not None:
        stmt = stmt.where(HealthMetric.measured_at <= end_at)
    return list(
        db.scalars(stmt.order_by(HealthMetric.measured_at.desc()).limit(limit)),
    )


# 函数职责：列表查询流程，按过滤条件返回一组对象，并保持排序、分页或范围语义稳定。
# 业务边界：返回集合时要避免把未授权数据暴露给调用方。
def list_recent_metrics(
    db: Session,
    user_id: UUID,
    *,
    metric_types: list[MetricType] | None = None,
    days: int = 7,
    limit_per_type: int = 20,
) -> list[HealthMetric]:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    start_at = datetime.now(timezone.utc) - timedelta(days=days)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if not metric_types:
        return list_metrics(db, user_id, start_at=start_at, limit=limit_per_type)
    records: list[HealthMetric] = []
    # 循环说明：逐项处理集合中的业务对象，保持每个元素处理逻辑一致。
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


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_latest_metric(
    db: Session,
    user_id: UUID,
    metric_type: MetricType,
) -> HealthMetric | None:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    return db.scalar(
        select(HealthMetric)
        .where(HealthMetric.user_id == user_id, HealthMetric.metric_type == metric_type)
        .order_by(HealthMetric.measured_at.desc())
        .limit(1),
    )


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
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
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
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


# 函数职责：列表查询流程，按过滤条件返回一组对象，并保持排序、分页或范围语义稳定。
# 业务边界：返回集合时要避免把未授权数据暴露给调用方。
def list_blood_pressure_records(
    db: Session,
    user_id: UUID,
    *,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    limit: int = 100,
) -> list[BloodPressureRecord]:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    stmt = select(BloodPressureRecord).where(BloodPressureRecord.user_id == user_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if start_at is not None:
        stmt = stmt.where(BloodPressureRecord.measured_at >= start_at)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if end_at is not None:
        stmt = stmt.where(BloodPressureRecord.measured_at <= end_at)
    return list(
        db.scalars(stmt.order_by(BloodPressureRecord.measured_at.desc()).limit(limit)),
    )


# 函数职责：列表查询流程，按过滤条件返回一组对象，并保持排序、分页或范围语义稳定。
# 业务边界：返回集合时要避免把未授权数据暴露给调用方。
def list_recent_blood_pressure(
    db: Session,
    user_id: UUID,
    *,
    days: int = 30,
    limit: int = 30,
) -> list[BloodPressureRecord]:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    start_at = datetime.now(timezone.utc) - timedelta(days=days)
    return list_blood_pressure_records(db, user_id, start_at=start_at, limit=limit)


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_latest_blood_pressure(
    db: Session,
    user_id: UUID,
) -> BloodPressureRecord | None:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    return db.scalar(
        select(BloodPressureRecord)
        .where(BloodPressureRecord.user_id == user_id)
        .order_by(BloodPressureRecord.measured_at.desc())
        .limit(1),
    )


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
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
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
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


# 函数职责：更新流程，在校验当前状态后修改已有对象或推进状态机。
# 业务边界：更新动作要保持幂等性和状态合法性，避免跳过必要确认。
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
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    job = get_import_job(db, job_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if job is None:
        return None
    job.status = status
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if total_count is not None:
        job.total_count = total_count
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if success_count is not None:
        job.success_count = success_count
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if failed_count is not None:
        job.failed_count = failed_count
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if error_message is not None:
        job.error_message = error_message
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if started_at is not None:
        job.started_at = started_at
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if finished_at is not None:
        job.finished_at = finished_at
    db.flush()
    return job


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_import_job(db: Session, job_id: UUID) -> HealthDataImportJob | None:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    return db.get(HealthDataImportJob, job_id)


# 函数职责：列表查询流程，按过滤条件返回一组对象，并保持排序、分页或范围语义稳定。
# 业务边界：返回集合时要避免把未授权数据暴露给调用方。
def list_import_jobs(
    db: Session,
    user_id: UUID,
    *,
    status: HealthDataImportStatus | None = None,
    limit: int = 50,
) -> list[HealthDataImportJob]:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    stmt = select(HealthDataImportJob).where(HealthDataImportJob.user_id == user_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if status is not None:
        stmt = stmt.where(HealthDataImportJob.status == status)
    return list(db.scalars(stmt.order_by(HealthDataImportJob.created_at.desc()).limit(limit)))
