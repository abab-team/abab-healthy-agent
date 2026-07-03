from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utc_now
from app.modules.permissions.enums import PermissionAuditAction


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class MemberSharePermission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "member_share_permissions"

    family_id: Mapped[UUID] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    share_all: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_view_profile: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    can_view_metrics: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    can_view_reports: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    can_view_symptoms: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    can_view_medical_events: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    can_view_documents: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    can_view_alerts: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    can_view_memory_summary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    can_create_symptom_records: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    can_create_metric_records: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    can_upload_documents: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    can_create_medical_events: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    can_generate_reports: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    can_generate_doctor_visit_summary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    can_export_summary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "family_id",
            "user_id",
            name="uq_member_share_permissions_family_id_user_id",
        ),
        Index("ix_member_share_permissions_family_id", "family_id"),
        Index("ix_member_share_permissions_user_id", "user_id"),
        Index("ix_member_share_permissions_share_all", "share_all"),
    )


class PermissionAuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "permission_audit_logs"

    family_id: Mapped[UUID] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    target_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    action: Mapped[PermissionAuditAction] = mapped_column(
        Enum(
            PermissionAuditAction,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    permission_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    before_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_permission_audit_logs_family_id", "family_id"),
        Index("ix_permission_audit_logs_actor_user_id", "actor_user_id"),
        Index("ix_permission_audit_logs_target_user_id", "target_user_id"),
        Index("ix_permission_audit_logs_action", "action"),
        Index("ix_permission_audit_logs_created_at", "created_at"),
    )
