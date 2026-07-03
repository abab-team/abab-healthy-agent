from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utc_now
from app.modules.alerts.enums import (
    AlertEventType,
    AlertLevel,
    AlertSource,
    AlertStatus,
    AlertType,
)


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class Alert(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "alerts"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    alert_type: Mapped[AlertType] = mapped_column(
        Enum(
            AlertType,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    level: Mapped[AlertLevel] = mapped_column(
        Enum(
            AlertLevel,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=AlertLevel.INFO,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_action: Mapped[str | None] = mapped_column(String(500), nullable=True)
    related_entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    related_entity_id: Mapped[UUID | None] = mapped_column(nullable=True)
    trigger_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[AlertStatus] = mapped_column(
        Enum(
            AlertStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=AlertStatus.ACTIVE,
    )
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    source: Mapped[AlertSource] = mapped_column(
        Enum(
            AlertSource,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=AlertSource.RULE,
    )

    __table_args__ = (
        Index("ix_alerts_user_id", "user_id"),
        Index("ix_alerts_family_id", "family_id"),
        Index("ix_alerts_alert_type", "alert_type"),
        Index("ix_alerts_level", "level"),
        Index("ix_alerts_status", "status"),
        Index("ix_alerts_due_at", "due_at"),
        Index(
            "ix_alerts_related_entity_type_related_entity_id",
            "related_entity_type",
            "related_entity_id",
        ),
        Index("ix_alerts_created_at", "created_at"),
    )


class AlertEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "alert_events"

    alert_id: Mapped[UUID] = mapped_column(
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[AlertEventType] = mapped_column(
        Enum(
            AlertEventType,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    before_status: Mapped[AlertStatus | None] = mapped_column(
        Enum(
            AlertStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=True,
    )
    after_status: Mapped[AlertStatus | None] = mapped_column(
        Enum(
            AlertStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=True,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_alert_events_alert_id", "alert_id"),
        Index("ix_alert_events_actor_user_id", "actor_user_id"),
        Index("ix_alert_events_event_type", "event_type"),
        Index("ix_alert_events_created_at", "created_at"),
    )
