# 模块领域：健康指标模块
# 领域说明：负责血压、体重、睡眠、活动等可量化指标的录入、查询和统计。
# 文件职责：业务服务文件。编排领域规则、权限校验、仓储调用和状态流转，是模块的主要业务入口。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.health_data import repository, stats
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
from app.modules.health_data.exceptions import (
    HealthDataImportJobNotFoundError,
    InvalidBloodPressureValueError,
    InvalidMetricValueError,
)
from app.modules.health_data.models import BloodPressureRecord, HealthMetric
from app.modules.health_data.schemas import BloodPressureSummary, MetricSummary


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def add_metric(
    db: Session,
    *,
    user_id: UUID,
    metric_type: MetricType | str,
    value_numeric: float | None = None,
    value_text: str | None = None,
    unit: str | None = None,
    measured_at: datetime | None = None,
    source: MetricSource | str = MetricSource.MANUAL,
    confidence_level: ConfidenceLevel | str = ConfidenceLevel.HIGH,
    note: str | None = None,
) -> HealthMetric:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    metric_type = _coerce_enum(MetricType, metric_type)
    source = _coerce_enum(MetricSource, source)
    confidence_level = _coerce_enum(ConfidenceLevel, confidence_level)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if value_numeric is None and value_text is None:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise InvalidMetricValueError("value_numeric or value_text is required")
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if value_numeric is not None and not isinstance(value_numeric, int | float):
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise InvalidMetricValueError("value_numeric must be numeric")
    return repository.create_metric(
        db,
        user_id=user_id,
        metric_type=metric_type,
        value_numeric=value_numeric,
        value_text=value_text,
        unit=unit,
        measured_at=measured_at or datetime.now(timezone.utc),
        source=source,
        confidence_level=confidence_level,
        note=note,
    )


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_recent_metrics(
    db: Session,
    *,
    user_id: UUID,
    metric_types: list[MetricType | str] | None = None,
    days: int = 7,
) -> list[HealthMetric]:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    coerced = [_coerce_enum(MetricType, item) for item in metric_types] if metric_types else None
    return repository.list_recent_metrics(db, user_id, metric_types=coerced, days=days)


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_latest_metrics_snapshot(
    db: Session,
    *,
    user_id: UUID,
    metric_types: list[MetricType | str] | None = None,
) -> dict[str, dict | None]:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    coerced = [_coerce_enum(MetricType, item) for item in metric_types] if metric_types else list(MetricType)
    snapshot: dict[str, dict | None] = {}
    # 循环说明：逐项处理集合中的业务对象，保持每个元素处理逻辑一致。
    for metric_type in coerced:
        latest = repository.get_latest_metric(db, user_id, metric_type)
        snapshot[metric_type.value] = _metric_record_dict(latest) if latest else None
    return snapshot


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_metric_summary(
    db: Session,
    *,
    user_id: UUID,
    metric_type: MetricType | str,
    days: int = 7,
) -> MetricSummary:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    metric_type = _coerce_enum(MetricType, metric_type)
    records = repository.list_recent_metrics(
        db,
        user_id,
        metric_types=[metric_type],
        days=days,
        limit_per_type=100,
    )
    numeric_values = [stats.to_float(record.value_numeric) for record in records if record.value_numeric is not None]
    numeric_values = [value for value in numeric_values if value is not None]
    latest = records[0] if records else None
    latest_value = None
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if latest is not None:
        latest_value = stats.to_float(latest.value_numeric) if latest.value_numeric is not None else latest.value_text
    return MetricSummary(
        metric_type=metric_type.value,
        days=days,
        count=len(records),
        latest_value=latest_value,
        latest_measured_at=latest.measured_at if latest else None,
        min_value=min(numeric_values) if numeric_values else None,
        max_value=max(numeric_values) if numeric_values else None,
        avg_value=stats.average(numeric_values),
        unit=latest.unit if latest else None,
        data_quality=stats.data_quality_for_count(len(records)),
        records=[_metric_record_dict(record) for record in records],
    )


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def add_blood_pressure_record(
    db: Session,
    *,
    user_id: UUID,
    systolic: int,
    diastolic: int,
    pulse: int | None = None,
    measured_at: datetime | None = None,
    measurement_context: BloodPressureMeasurementContext | str = BloodPressureMeasurementContext.UNKNOWN,
    arm: BloodPressureArm | str = BloodPressureArm.UNKNOWN,
    posture: BloodPressurePosture | str = BloodPressurePosture.UNKNOWN,
    source: MetricSource | str = MetricSource.MANUAL,
    confidence_level: ConfidenceLevel | str = ConfidenceLevel.HIGH,
    note: str | None = None,
) -> BloodPressureRecord:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    _validate_blood_pressure_values(systolic, diastolic, pulse)
    return repository.create_blood_pressure_record(
        db,
        user_id=user_id,
        systolic=systolic,
        diastolic=diastolic,
        pulse=pulse,
        measured_at=measured_at or datetime.now(timezone.utc),
        measurement_context=_coerce_enum(BloodPressureMeasurementContext, measurement_context),
        arm=_coerce_enum(BloodPressureArm, arm),
        posture=_coerce_enum(BloodPressurePosture, posture),
        source=_coerce_enum(MetricSource, source),
        confidence_level=_coerce_enum(ConfidenceLevel, confidence_level),
        note=note,
    )


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_recent_blood_pressure(
    db: Session,
    *,
    user_id: UUID,
    days: int = 30,
) -> list[BloodPressureRecord]:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    return repository.list_recent_blood_pressure(db, user_id, days=days)


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_blood_pressure_summary(
    db: Session,
    *,
    user_id: UUID,
    days: int = 30,
) -> BloodPressureSummary:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    records = get_recent_blood_pressure(db, user_id=user_id, days=days)
    latest = records[0] if records else None
    systolic_values = [record.systolic for record in records]
    diastolic_values = [record.diastolic for record in records]
    return BloodPressureSummary(
        days=days,
        count=len(records),
        latest_systolic=latest.systolic if latest else None,
        latest_diastolic=latest.diastolic if latest else None,
        latest_pulse=latest.pulse if latest else None,
        latest_measured_at=latest.measured_at if latest else None,
        avg_systolic=stats.average([float(value) for value in systolic_values]),
        avg_diastolic=stats.average([float(value) for value in diastolic_values]),
        min_systolic=min(systolic_values) if systolic_values else None,
        max_systolic=max(systolic_values) if systolic_values else None,
        min_diastolic=min(diastolic_values) if diastolic_values else None,
        max_diastolic=max(diastolic_values) if diastolic_values else None,
        data_quality=stats.data_quality_for_count(len(records)),
        records=[_blood_pressure_record_dict(record) for record in records],
    )


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def create_import_job(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID | None = None,
    import_type: HealthDataImportType | str = HealthDataImportType.MANUAL_BATCH,
    source: MetricSource | str = MetricSource.MANUAL,
    file_name: str | None = None,
    file_path: str | None = None,
):
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    return repository.create_import_job(
        db,
        user_id=user_id,
        family_id=family_id,
        import_type=_coerce_enum(HealthDataImportType, import_type),
        source=_coerce_enum(MetricSource, source),
        file_name=file_name,
        file_path=file_path,
    )


# 函数职责：更新流程，在校验当前状态后修改已有对象或推进状态机。
# 业务边界：更新动作要保持幂等性和状态合法性，避免跳过必要确认。
def mark_import_job_started(db: Session, job_id: UUID):
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    job = repository.update_import_job_status(
        db,
        job_id,
        HealthDataImportStatus.PROCESSING,
        started_at=datetime.now(timezone.utc),
    )
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if job is None:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise HealthDataImportJobNotFoundError("import job not found")
    return job


# 函数职责：更新流程，在校验当前状态后修改已有对象或推进状态机。
# 业务边界：更新动作要保持幂等性和状态合法性，避免跳过必要确认。
def mark_import_job_finished(
    db: Session,
    job_id: UUID,
    *,
    total_count: int,
    success_count: int,
    failed_count: int,
    error_message: str | None = None,
):
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    status = HealthDataImportStatus.SUCCESS if failed_count == 0 else HealthDataImportStatus.PARTIAL_SUCCESS
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if success_count == 0 and failed_count > 0:
        status = HealthDataImportStatus.FAILED
    job = repository.update_import_job_status(
        db,
        job_id,
        status,
        total_count=total_count,
        success_count=success_count,
        failed_count=failed_count,
        error_message=error_message,
        finished_at=datetime.now(timezone.utc),
    )
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if job is None:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise HealthDataImportJobNotFoundError("import job not found")
    return job


# 函数职责：业务函数，封装 健康指标模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def get_archive_trends(
    db: Session,
    *,
    user_id: UUID,
    metric_types: list[MetricType | str] | None = None,
    days: int = 90,
) -> dict:
    selected = [_coerce_enum(MetricType, item) for item in metric_types] if metric_types else [
        MetricType.SLEEP_DURATION,
        MetricType.STEPS,
        MetricType.WEIGHT,
    ]
    series: list[dict] = []
    for metric_type in selected:
        summary = get_metric_summary(db, user_id=user_id, metric_type=metric_type, days=days)
        series.append(
            {
                "metric_type": summary.metric_type,
                "label": _metric_label(summary.metric_type),
                "unit": summary.unit,
                "count": summary.count,
                "points": [
                    {
                        "measured_at": record["measured_at"],
                        "value": record["value_numeric"],
                        "unit": record.get("unit"),
                    }
                    for record in reversed(summary.records)
                    if record.get("value_numeric") is not None
                ],
                "summary": _trend_summary_text(summary.metric_type, summary.count),
                "data_quality": summary.data_quality,
            },
        )
    bp_summary = get_blood_pressure_summary(db, user_id=user_id, days=days)
    series.append(
        {
            "metric_type": "blood_pressure",
            "label": "血压",
            "unit": "mmHg",
            "count": bp_summary.count,
            "points": [
                {
                    "measured_at": record["measured_at"],
                    "systolic": record["systolic"],
                    "diastolic": record["diastolic"],
                    "pulse": record.get("pulse"),
                }
                for record in reversed(bp_summary.records)
            ],
            "summary": _trend_summary_text("blood_pressure", bp_summary.count),
            "data_quality": bp_summary.data_quality,
        },
    )
    return {
        "days": days,
        "generated_from": "system_records",
        "disclaimer": "Based on system records only; this trend view does not replace doctor judgment.",
        "series": series,
    }


def preview_health_data_import(
    *,
    rows: list[dict],
    import_type: HealthDataImportType | str = HealthDataImportType.CSV,
    file_name: str | None = None,
) -> dict:
    import_type = _coerce_enum(HealthDataImportType, import_type)
    preview_rows: list[dict] = []
    errors: list[dict] = []
    for index, row in enumerate(rows):
        normalized, row_errors = _normalize_import_row(row, index=index)
        if row_errors:
            errors.extend(row_errors)
        else:
            preview_rows.append(normalized)
    return {
        "import_type": import_type.value,
        "file_name": file_name,
        "total_count": len(rows),
        "valid_count": len(preview_rows),
        "invalid_count": len(errors),
        "preview_rows": preview_rows[:50],
        "errors": errors[:50],
        "will_write": False,
        "disclaimer": "Preview only. No health records are written until confirmation.",
    }


def confirm_health_data_import(
    db: Session,
    *,
    user_id: UUID,
    rows: list[dict],
    import_type: HealthDataImportType | str = HealthDataImportType.CSV,
    file_name: str | None = None,
    confirmation: bool = False,
) -> dict:
    preview = preview_health_data_import(rows=rows, import_type=import_type, file_name=file_name)
    if not confirmation:
        return {
            **preview,
            "job_id": None,
            "status": HealthDataImportStatus.PENDING.value,
            "created_records_count": 0,
        }
    job = create_import_job(
        db,
        user_id=user_id,
        import_type=preview["import_type"],
        source=MetricSource.IMPORTED,
        file_name=file_name,
        file_path=None,
    )
    mark_import_job_started(db, job.id)
    created = 0
    for row in preview["preview_rows"]:
        if row["metric_type"] == "blood_pressure":
            add_blood_pressure_record(
                db,
                user_id=user_id,
                systolic=row["systolic"],
                diastolic=row["diastolic"],
                pulse=row.get("pulse"),
                measured_at=row["measured_at"],
                source=MetricSource.IMPORTED,
                confidence_level=ConfidenceLevel.MEDIUM,
                note=row.get("note"),
            )
        else:
            add_metric(
                db,
                user_id=user_id,
                metric_type=row["metric_type"],
                value_numeric=row["value_numeric"],
                unit=row.get("unit"),
                measured_at=row["measured_at"],
                source=MetricSource.IMPORTED,
                confidence_level=ConfidenceLevel.MEDIUM,
                note=row.get("note"),
            )
        created += 1
    status_job = mark_import_job_finished(
        db,
        job.id,
        total_count=preview["total_count"],
        success_count=created,
        failed_count=preview["invalid_count"],
        error_message="Some rows were skipped during import preview." if preview["invalid_count"] else None,
    )
    return {
        **preview,
        "job_id": status_job.id,
        "status": status_job.status.value,
        "created_records_count": created,
        "will_write": True,
        "disclaimer": "Confirmed import wrote only validated system records. It does not make medical judgments.",
    }


def _validate_blood_pressure_values(
    systolic: int,
    diastolic: int,
    pulse: int | None,
) -> None:
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    if not isinstance(systolic, int) or not isinstance(diastolic, int):
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise InvalidBloodPressureValueError("systolic and diastolic must be integers")
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if not 40 <= systolic <= 260:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise InvalidBloodPressureValueError("systolic is outside accepted recording range")
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if not 30 <= diastolic <= 180:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise InvalidBloodPressureValueError("diastolic is outside accepted recording range")
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if pulse is not None and (not isinstance(pulse, int) or not 30 <= pulse <= 220):
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise InvalidBloodPressureValueError("pulse is outside accepted recording range")


# 函数职责：业务函数，封装 健康指标模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def _coerce_enum(enum_cls: type[StrEnum], value):
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    if isinstance(value, enum_cls):
        return value
    return enum_cls(value)


# 函数职责：业务函数，封装 健康指标模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def _metric_record_dict(record: HealthMetric) -> dict:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    return {
        "id": str(record.id),
        "metric_type": record.metric_type.value,
        "value_numeric": stats.to_float(record.value_numeric),
        "value_text": record.value_text,
        "unit": record.unit,
        "measured_at": record.measured_at,
    }


# 函数职责：业务函数，封装 健康指标模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def _blood_pressure_record_dict(record: BloodPressureRecord) -> dict:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    return {
        "id": str(record.id),
        "systolic": record.systolic,
        "diastolic": record.diastolic,
        "pulse": record.pulse,
        "measured_at": record.measured_at,
    }


def _metric_label(metric_type: str) -> str:
    labels = {
        "sleep_duration": "睡眠",
        "steps": "步数",
        "weight": "体重",
        "bmi": "BMI",
        "heart_rate": "心率",
    }
    return labels.get(metric_type, metric_type.replace("_", " "))


def _trend_summary_text(metric_type: str, count: int) -> str:
    if count == 0:
        return "No system records in this range."
    return f"{count} system record(s) in this range. This is a data summary only."


def _normalize_import_row(row: dict, *, index: int) -> tuple[dict, list[dict]]:
    errors: list[dict] = []
    raw_metric_type = row.get("metric_type")
    measured_at = row.get("measured_at")
    if isinstance(measured_at, str):
        try:
            measured_at = datetime.fromisoformat(measured_at.replace("Z", "+00:00"))
        except ValueError:
            errors.append({"row": index, "field": "measured_at", "message": "invalid datetime"})
    if measured_at is None:
        errors.append({"row": index, "field": "measured_at", "message": "required"})
    metric_type = str(raw_metric_type.value if isinstance(raw_metric_type, MetricType) else raw_metric_type or "")
    if metric_type in {"blood_pressure", "blood-pressure"}:
        systolic = row.get("systolic")
        diastolic = row.get("diastolic")
        pulse = row.get("pulse")
        try:
            _validate_blood_pressure_values(int(systolic), int(diastolic), int(pulse) if pulse is not None else None)
        except (TypeError, ValueError, InvalidBloodPressureValueError):
            errors.append({"row": index, "field": "blood_pressure", "message": "invalid blood pressure values"})
        if errors:
            return {}, errors
        return {
            "metric_type": "blood_pressure",
            "measured_at": measured_at,
            "systolic": int(systolic),
            "diastolic": int(diastolic),
            "pulse": int(pulse) if pulse is not None else None,
            "note": row.get("note"),
        }, []
    try:
        metric = _coerce_enum(MetricType, metric_type)
    except ValueError:
        errors.append({"row": index, "field": "metric_type", "message": "unsupported metric type"})
        return {}, errors
    value_numeric = row.get("value_numeric")
    if value_numeric is None:
        errors.append({"row": index, "field": "value_numeric", "message": "required for metric import"})
    try:
        numeric = float(value_numeric)
    except (TypeError, ValueError):
        errors.append({"row": index, "field": "value_numeric", "message": "must be numeric"})
        numeric = None
    if numeric is not None and numeric < 0:
        errors.append({"row": index, "field": "value_numeric", "message": "must be non-negative"})
    if errors:
        return {}, errors
    return {
        "metric_type": metric.value,
        "measured_at": measured_at,
        "value_numeric": numeric,
        "unit": row.get("unit"),
        "note": row.get("note"),
    }, []
