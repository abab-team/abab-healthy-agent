# 模块领域：家庭成员模块
# 领域说明：负责家庭、成员关系、邀请流程和自然语言成员称呼解析。
# 文件职责：数据模型文件。定义数据库表、字段、索引和表之间的关系，是业务数据持久化的核心。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

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


# 函数职责：业务函数，封装 家庭成员模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return [item.value for item in enum_cls]


# 类职责：Family 是 家庭成员模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class Family(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "families"

    # 字段说明：name 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 字段说明：owner_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    owner_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # 字段说明：members 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    members: Mapped[list[FamilyMember]] = relationship(
        back_populates="family",
        cascade="all, delete-orphan",
    )
    # 字段说明：invitations 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    invitations: Mapped[list[FamilyInvitation]] = relationship(
        back_populates="family",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("ix_families_owner_user_id", "owner_user_id"),)


# 类职责：FamilyMember 是 家庭成员模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class FamilyMember(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "family_members"

    # 字段说明：family_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    family_id: Mapped[UUID] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：role 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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
    # 字段说明：relationship_label 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    relationship_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：display_name 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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
    # 字段说明：joined_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # 字段说明：family 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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


# 类职责：FamilyInvitation 是 家庭成员模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class FamilyInvitation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "family_invitations"

    # 字段说明：family_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    family_id: Mapped[UUID] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：inviter_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    inviter_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # 字段说明：invite_code 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    invite_code: Mapped[str] = mapped_column(String(64), nullable=False)
    # 字段说明：invitee_phone 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    invitee_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # 字段说明：invitee_email 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    invitee_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 字段说明：status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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
    # 字段说明：expires_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    # 字段说明：accepted_by_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    accepted_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：accepted_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # 字段说明：family 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    family: Mapped[Family] = relationship(back_populates="invitations")

    __table_args__ = (
        UniqueConstraint("invite_code", name="uq_family_invitations_invite_code"),
        Index("ix_family_invitations_family_id", "family_id"),
        Index("ix_family_invitations_status", "status"),
        Index("ix_family_invitations_expires_at", "expires_at"),
    )
