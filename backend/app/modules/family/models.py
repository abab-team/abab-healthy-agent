from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utc_now
from app.modules.family.enums import (
    FamilyInvitationStatus,
    FamilyMemberStatus,
    FamilyRole,
)


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class Family(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "families"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    members: Mapped[list[FamilyMember]] = relationship(
        back_populates="family",
        cascade="all, delete-orphan",
    )
    invitations: Mapped[list[FamilyInvitation]] = relationship(
        back_populates="family",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("ix_families_owner_user_id", "owner_user_id"),)


class FamilyMember(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "family_members"

    family_id: Mapped[UUID] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[FamilyRole] = mapped_column(
        Enum(
            FamilyRole,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=FamilyRole.MEMBER,
    )
    # Family-scoped relationship label, not a user's global identity.
    relationship_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[FamilyMemberStatus] = mapped_column(
        Enum(
            FamilyMemberStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=FamilyMemberStatus.ACTIVE,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    family: Mapped[Family] = relationship(back_populates="members")

    __table_args__ = (
        UniqueConstraint(
            "family_id",
            "user_id",
            name="uq_family_members_family_id_user_id",
        ),
        Index("ix_family_members_family_id", "family_id"),
        Index("ix_family_members_user_id", "user_id"),
        Index("ix_family_members_status", "status"),
    )


class FamilyInvitation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "family_invitations"

    family_id: Mapped[UUID] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=False,
    )
    inviter_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    invite_code: Mapped[str] = mapped_column(String(64), nullable=False)
    invitee_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    invitee_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[FamilyInvitationStatus] = mapped_column(
        Enum(
            FamilyInvitationStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=FamilyInvitationStatus.PENDING,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    accepted_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    family: Mapped[Family] = relationship(back_populates="invitations")

    __table_args__ = (
        UniqueConstraint("invite_code", name="uq_family_invitations_invite_code"),
        Index("ix_family_invitations_family_id", "family_id"),
        Index("ix_family_invitations_status", "status"),
        Index("ix_family_invitations_expires_at", "expires_at"),
    )
