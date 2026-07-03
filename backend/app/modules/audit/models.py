from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import UUIDPrimaryKeyMixin, utc_now
from app.modules.audit.enums import (
    AuditAction,
    AuditResourceType,
    DataAccessAction,
    DataAccessCategory,
    PrivacyEventType,
)


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class AuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_logs"

    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[AuditAction] = mapped_column(
        Enum(
            AuditAction,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    resource_type: Mapped[AuditResourceType] = mapped_column(
        Enum(
            AuditResourceType,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    resource_id: Mapped[UUID | None] = mapped_column(nullable=True)
    target_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_audit_logs_actor_user_id", "actor_user_id"),
        Index("ix_audit_logs_family_id", "family_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_resource_type", "resource_type"),
        Index("ix_audit_logs_resource_id", "resource_id"),
        Index("ix_audit_logs_target_user_id", "target_user_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )


class DataAccessLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "data_access_logs"

    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    data_category: Mapped[DataAccessCategory] = mapped_column(
        Enum(
            DataAccessCategory,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    action: Mapped[DataAccessAction] = mapped_column(
        Enum(
            DataAccessAction,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    access_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    permission_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_data_access_logs_request_id", "request_id"),
        Index("ix_data_access_logs_actor_user_id", "actor_user_id"),
        Index("ix_data_access_logs_family_id", "family_id"),
        Index("ix_data_access_logs_target_user_id", "target_user_id"),
        Index("ix_data_access_logs_data_category", "data_category"),
        Index("ix_data_access_logs_action", "action"),
        Index("ix_data_access_logs_allowed", "allowed"),
        Index("ix_data_access_logs_resource_type", "resource_type"),
        Index("ix_data_access_logs_resource_id", "resource_id"),
        Index("ix_data_access_logs_created_at", "created_at"),
    )


class PrivacyEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "privacy_events"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[PrivacyEventType] = mapped_column(
        Enum(
            PrivacyEventType,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_privacy_events_user_id", "user_id"),
        Index("ix_privacy_events_actor_user_id", "actor_user_id"),
        Index("ix_privacy_events_family_id", "family_id"),
        Index("ix_privacy_events_event_type", "event_type"),
        Index("ix_privacy_events_created_at", "created_at"),
    )
