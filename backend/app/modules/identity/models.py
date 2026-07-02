from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utc_now
from app.modules.identity.enums import AuthProvider, Gender, UserStatus


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    phone: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    gender: Mapped[Gender | None] = mapped_column(
        Enum(
            Gender,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=True,
    )
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[UserStatus] = mapped_column(
        Enum(
            UserStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=UserStatus.ACTIVE,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    auth_accounts: Mapped[list[UserAuthAccount]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    login_sessions: Mapped[list[LoginSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_users_phone", "phone"),
        Index("ix_users_email", "email"),
        Index("ix_users_status", "status"),
    )


class UserAuthAccount(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "user_auth_accounts"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[AuthProvider] = mapped_column(
        Enum(
            AuthProvider,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    union_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="auth_accounts")

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_user_id",
            name="uq_user_auth_accounts_provider_provider_user_id",
        ),
        Index("ix_user_auth_accounts_user_id", "user_id"),
        Index("ix_user_auth_accounts_provider_user_id", "provider_user_id"),
    )


class LoginSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "login_sessions"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped[User] = relationship(back_populates="login_sessions")

    __table_args__ = (
        Index("ix_login_sessions_user_id", "user_id"),
        Index("ix_login_sessions_session_token_hash", "session_token_hash", unique=True),
        Index("ix_login_sessions_expires_at", "expires_at"),
    )


class RefreshToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped[User] = relationship(back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_tokens_user_id", "user_id"),
        Index("ix_refresh_tokens_token_hash", "token_hash", unique=True),
        Index("ix_refresh_tokens_expires_at", "expires_at"),
    )
