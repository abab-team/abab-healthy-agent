# 模块领域：健康指标模块
# 领域说明：负责血压、体重、睡眠、活动等可量化指标的录入、查询和统计。
# 文件职责：数据模型文件。定义数据库表、字段、索引和表之间的关系，是业务数据持久化的核心。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
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


# 函数职责：业务函数，封装 健康指标模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return [item.value for item in enum_cls]


# 类职责：HealthMetric 是 健康指标模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class HealthMetric(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "health_metrics"

    # 字段说明：user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：metric_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    metric_type: Mapped[MetricType] = mapped_column(
        Enum(
            MetricType,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    # 字段说明：value_numeric 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    value_numeric: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    # 字段说明：value_text 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    value_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 字段说明：unit 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # 字段说明：measured_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    # 字段说明：period_start 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # 字段说明：period_end 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # 字段说明：source 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    source: Mapped[MetricSource] = mapped_column(
        Enum(
            MetricSource,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=MetricSource.UNKNOWN,
    )
    # 字段说明：source_detail 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    source_detail: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 字段说明：confidence_level 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    confidence_level: Mapped[ConfidenceLevel] = mapped_column(
        Enum(
            ConfidenceLevel,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=ConfidenceLevel.UNKNOWN,
    )
    # 字段说明：note 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_health_metrics_user_id", "user_id"),
        Index("ix_health_metrics_metric_type", "metric_type"),
        Index("ix_health_metrics_measured_at", "measured_at"),
        Index("ix_health_metrics_source", "source"),
        Index(
            "ix_health_metrics_user_id_metric_type_measured_at",
            "user_id",
            "metric_type",
            "measured_at",
        ),
    )


# 类职责：BloodPressureRecord 是 健康指标模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class BloodPressureRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "blood_pressure_records"

    # 字段说明：user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：systolic 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    systolic: Mapped[int] = mapped_column(Integer, nullable=False)
    # 字段说明：diastolic 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    diastolic: Mapped[int] = mapped_column(Integer, nullable=False)
    # 字段说明：pulse 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    pulse: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 字段说明：measured_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    # 字段说明：measurement_context 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    measurement_context: Mapped[BloodPressureMeasurementContext] = mapped_column(
        Enum(
            BloodPressureMeasurementContext,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=BloodPressureMeasurementContext.UNKNOWN,
    )
    # 字段说明：arm 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    arm: Mapped[BloodPressureArm] = mapped_column(
        Enum(
            BloodPressureArm,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=BloodPressureArm.UNKNOWN,
    )
    # 字段说明：posture 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    posture: Mapped[BloodPressurePosture] = mapped_column(
        Enum(
            BloodPressurePosture,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=BloodPressurePosture.UNKNOWN,
    )
    # 字段说明：source 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    source: Mapped[MetricSource] = mapped_column(
        Enum(
            MetricSource,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=MetricSource.UNKNOWN,
    )
    # 字段说明：confidence_level 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    confidence_level: Mapped[ConfidenceLevel] = mapped_column(
        Enum(
            ConfidenceLevel,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=ConfidenceLevel.UNKNOWN,
    )
    # 字段说明：note 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_blood_pressure_records_user_id", "user_id"),
        Index("ix_blood_pressure_records_measured_at", "measured_at"),
        Index("ix_blood_pressure_records_systolic", "systolic"),
        Index("ix_blood_pressure_records_diastolic", "diastolic"),
        Index(
            "ix_blood_pressure_records_user_id_measured_at",
            "user_id",
            "measured_at",
        ),
    )


# 类职责：HealthDataImportJob 是 健康指标模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class HealthDataImportJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "health_data_import_jobs"

    # 字段说明：user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：family_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：import_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    import_type: Mapped[HealthDataImportType] = mapped_column(
        Enum(
            HealthDataImportType,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    # 字段说明：source 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    source: Mapped[MetricSource] = mapped_column(
        Enum(
            MetricSource,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=MetricSource.UNKNOWN,
    )
    # 字段说明：file_name 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 字段说明：file_path 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # 字段说明：status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    status: Mapped[HealthDataImportStatus] = mapped_column(
        Enum(
            HealthDataImportStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=HealthDataImportStatus.PENDING,
    )
    # 字段说明：total_count 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    total_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 字段说明：success_count 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 字段说明：failed_count 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 字段说明：error_message 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 字段说明：started_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # 字段说明：finished_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_health_data_import_jobs_user_id", "user_id"),
        Index("ix_health_data_import_jobs_family_id", "family_id"),
        Index("ix_health_data_import_jobs_status", "status"),
        Index("ix_health_data_import_jobs_source", "source"),
        Index("ix_health_data_import_jobs_created_at", "created_at"),
    )
