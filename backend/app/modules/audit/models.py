# 模块领域：审计模块
# 领域说明：负责记录敏感数据访问、隐私相关操作和 Agent 执行痕迹。
# 文件职责：数据模型文件。定义数据库表、字段、索引和表之间的关系，是业务数据持久化的核心。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

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


# 函数职责：业务函数，封装 审计模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return [item.value for item in enum_cls]


# 类职责：AuditLog 是 审计模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, Base。
class AuditLog(UUIDPrimaryKeyMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "audit_logs"

    # 字段说明：actor_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：family_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：action 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    action: Mapped[AuditAction] = mapped_column(
        Enum(
            AuditAction,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    # 字段说明：resource_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    resource_type: Mapped[AuditResourceType] = mapped_column(
        Enum(
            AuditResourceType,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    # 字段说明：resource_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    resource_id: Mapped[UUID | None] = mapped_column(nullable=True)
    # 字段说明：target_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    target_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：metadata_json 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # 字段说明：ip_address 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # 字段说明：user_agent 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # 字段说明：created_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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


# 类职责：DataAccessLog 是 审计模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, Base。
class DataAccessLog(UUIDPrimaryKeyMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "data_access_logs"

    # 字段说明：request_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：actor_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：family_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：target_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    target_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：data_category 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    data_category: Mapped[DataAccessCategory] = mapped_column(
        Enum(
            DataAccessCategory,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    # 字段说明：action 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    action: Mapped[DataAccessAction] = mapped_column(
        Enum(
            DataAccessAction,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    # 字段说明：access_reason 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    access_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 字段说明：allowed 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # 字段说明：permission_result 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    permission_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # 字段说明：resource_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：resource_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    resource_id: Mapped[UUID | None] = mapped_column(nullable=True)
    # 字段说明：created_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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


# 类职责：PrivacyEvent 是 审计模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, Base。
class PrivacyEvent(UUIDPrimaryKeyMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "privacy_events"

    # 字段说明：user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：actor_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：family_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：event_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    event_type: Mapped[PrivacyEventType] = mapped_column(
        Enum(
            PrivacyEventType,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    # 字段说明：details 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # 字段说明：created_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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
