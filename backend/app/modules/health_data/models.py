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


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class HealthMetric(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "health_metrics"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    metric_type: Mapped[MetricType] = mapped_column(
        Enum(
            MetricType,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    value_numeric: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    value_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
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
    source_detail: Mapped[str | None] = mapped_column(String(255), nullable=True)
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


class BloodPressureRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "blood_pressure_records"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    systolic: Mapped[int] = mapped_column(Integer, nullable=False)
    diastolic: Mapped[int] = mapped_column(Integer, nullable=False)
    pulse: Mapped[int | None] = mapped_column(Integer, nullable=True)
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
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


class HealthDataImportJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "health_data_import_jobs"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    import_type: Mapped[HealthDataImportType] = mapped_column(
        Enum(
            HealthDataImportType,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
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
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
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
    total_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
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
