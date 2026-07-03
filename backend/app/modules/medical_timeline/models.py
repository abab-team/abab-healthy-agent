from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.health_data.enums import ConfidenceLevel
from app.modules.medical_timeline.enums import (
    MedicalEventSource,
    MedicalEventStatus,
    MedicalEventType,
)


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class MedicalEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "medical_events"

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
    event_type: Mapped[MedicalEventType] = mapped_column(
        Enum(
            MedicalEventType,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    event_date_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hospital_or_org: Mapped[str | None] = mapped_column(String(200), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    diagnosis_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    doctor_advice: Mapped[str | None] = mapped_column(Text, nullable=True)
    medications: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    key_findings: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    follow_up_needed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    follow_up_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    related_document_id: Mapped[UUID | None] = mapped_column(nullable=True)
    source: Mapped[MedicalEventSource] = mapped_column(
        Enum(
            MedicalEventSource,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=MedicalEventSource.MANUAL,
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
    timeline_visible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    status: Mapped[MedicalEventStatus] = mapped_column(
        Enum(
            MedicalEventStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=MedicalEventStatus.ACTIVE,
    )

    __table_args__ = (
        Index("ix_medical_events_user_id", "user_id"),
        Index("ix_medical_events_family_id", "family_id"),
        Index("ix_medical_events_created_by_user_id", "created_by_user_id"),
        Index("ix_medical_events_event_type", "event_type"),
        Index("ix_medical_events_event_date", "event_date"),
        Index("ix_medical_events_follow_up_needed", "follow_up_needed"),
        Index("ix_medical_events_follow_up_at", "follow_up_at"),
        Index("ix_medical_events_status", "status"),
        Index("ix_medical_events_related_document_id", "related_document_id"),
        Index("ix_medical_events_created_at", "created_at"),
    )
