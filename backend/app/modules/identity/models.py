# 模块领域：用户身份模块
# 领域说明：负责用户账号、登录会话、认证令牌和第三方身份关联。
# 文件职责：数据模型文件。定义数据库表、字段、索引和表之间的关系，是业务数据持久化的核心。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utc_now
from app.modules.identity.enums import AuthProvider, Gender, UserStatus


# 函数职责：业务函数，封装 用户身份模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return [item.value for item in enum_cls]


# 类职责：User 是 用户身份模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "users"

    # 字段说明：phone 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True)
    # 字段说明：email 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    # 字段说明：password_hash 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 字段说明：nickname 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    nickname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：avatar_url 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # 字段说明：gender 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    gender: Mapped[Gender | None] = mapped_column(
        Enum(
            Gender,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=True,
    )
    # 字段说明：birth_date 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # 字段说明：status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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
    # 字段说明：last_login_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # 字段说明：auth_accounts 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    auth_accounts: Mapped[list[UserAuthAccount]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    # 字段说明：login_sessions 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    login_sessions: Mapped[list[LoginSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    # 字段说明：refresh_tokens 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_users_phone", "phone"),
        Index("ix_users_email", "email"),
        Index("ix_users_status", "status"),
    )


# 类职责：UserAuthAccount 是 用户身份模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, Base。
class UserAuthAccount(UUIDPrimaryKeyMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "user_auth_accounts"

    # 字段说明：user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：provider 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    provider: Mapped[AuthProvider] = mapped_column(
        Enum(
            AuthProvider,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    # 字段说明：provider_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    # 字段说明：union_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    union_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 字段说明：created_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # 字段说明：user 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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


# 类职责：LoginSession 是 用户身份模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class LoginSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "login_sessions"

    # 字段说明：user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：session_token_hash 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    session_token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # 字段说明：user_agent 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # 字段说明：ip_address 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # 字段说明：expires_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    # 字段说明：revoked_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # 字段说明：user 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    user: Mapped[User] = relationship(back_populates="login_sessions")

    __table_args__ = (
        Index("ix_login_sessions_user_id", "user_id"),
        Index("ix_login_sessions_session_token_hash", "session_token_hash", unique=True),
        Index("ix_login_sessions_expires_at", "expires_at"),
    )


# 类职责：RefreshToken 是 用户身份模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class RefreshToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "refresh_tokens"

    # 字段说明：user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：token_hash 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # 字段说明：expires_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    # 字段说明：revoked_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # 字段说明：user 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    user: Mapped[User] = relationship(back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_tokens_user_id", "user_id"),
        Index("ix_refresh_tokens_token_hash", "token_hash", unique=True),
        Index("ix_refresh_tokens_expires_at", "expires_at"),
    )
