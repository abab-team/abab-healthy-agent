from __future__ import annotations

from datetime import date
from enum import StrEnum
from uuid import UUID

from sqlalchemy import JSON, Date, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.reports.enums import (
    DailyReportGeneratedBy,
    DailyReportGenerationStatus,
    DailyReportStatusLevel,
)


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class DailyReport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "daily_reports"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    overall_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status_level: Mapped[DailyReportStatusLevel] = mapped_column(
        Enum(
            DailyReportStatusLevel,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=DailyReportStatusLevel.INSUFFICIENT_DATA,
    )
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    highlights: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    concerns: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    suggestions: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    metrics_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    related_symptom_record_ids: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    related_alert_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    generated_by: Mapped[DailyReportGeneratedBy] = mapped_column(
        Enum(
            DailyReportGeneratedBy,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=DailyReportGeneratedBy.SYSTEM,
    )
    generation_status: Mapped[DailyReportGenerationStatus] = mapped_column(
        Enum(
            DailyReportGenerationStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=DailyReportGenerationStatus.PENDING,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "report_date", name="uq_daily_reports_user_id_report_date"),
        Index("ix_daily_reports_user_id", "user_id"),
        Index("ix_daily_reports_family_id", "family_id"),
        Index("ix_daily_reports_report_date", "report_date"),
        Index("ix_daily_reports_status_level", "status_level"),
        Index("ix_daily_reports_generation_status", "generation_status"),
        Index("ix_daily_reports_created_at", "created_at"),
    )
