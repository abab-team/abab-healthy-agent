from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.health_data.enums import ConfidenceLevel
from app.modules.health_record.enums import (
    HealthRecordDraftStatus,
    HealthRecordDraftType,
    HealthRecordSource,
    SymptomRecordStatus,
)


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class SymptomRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "symptom_records"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    symptom_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    body_part: Mapped[str | None] = mapped_column(String(100), nullable=True)
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    occurrence_time_text: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    possible_trigger: Mapped[str | None] = mapped_column(String(255), nullable=True)
    related_metric_types: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    action_taken: Mapped[str | None] = mapped_column(String(500), nullable=True)
    follow_up_needed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    follow_up_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[SymptomRecordStatus] = mapped_column(
        Enum(
            SymptomRecordStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=SymptomRecordStatus.ACTIVE,
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
    ai_summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    timeline_visible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    source: Mapped[HealthRecordSource] = mapped_column(
        Enum(
            HealthRecordSource,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=HealthRecordSource.MANUAL,
    )

    __table_args__ = (
        Index("ix_symptom_records_user_id", "user_id"),
        Index("ix_symptom_records_family_id", "family_id"),
        Index("ix_symptom_records_created_by_user_id", "created_by_user_id"),
        Index("ix_symptom_records_symptom_name", "symptom_name"),
        Index("ix_symptom_records_started_at", "started_at"),
        Index("ix_symptom_records_follow_up_needed", "follow_up_needed"),
        Index("ix_symptom_records_status", "status"),
        Index("ix_symptom_records_created_at", "created_at"),
    )


class HealthRecordDraft(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "health_record_drafts"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    target_display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    draft_type: Mapped[HealthRecordDraftType] = mapped_column(
        Enum(
            HealthRecordDraftType,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    extracted_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    missing_fields: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    safety_flags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
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
    status: Mapped[HealthRecordDraftStatus] = mapped_column(
        Enum(
            HealthRecordDraftStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=HealthRecordDraftStatus.PENDING,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    confirmed_record_id: Mapped[UUID | None] = mapped_column(nullable=True)

    __table_args__ = (
        Index("ix_health_record_drafts_user_id", "user_id"),
        Index("ix_health_record_drafts_family_id", "family_id"),
        Index("ix_health_record_drafts_created_by_user_id", "created_by_user_id"),
        Index("ix_health_record_drafts_status", "status"),
        Index("ix_health_record_drafts_expires_at", "expires_at"),
        Index("ix_health_record_drafts_created_at", "created_at"),
    )
