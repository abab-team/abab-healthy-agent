# 模块领域：权限模块
# 领域说明：负责家庭成员之间的数据共享范围、访问策略和越权拦截。
# 文件职责：数据模型文件。定义数据库表、字段、索引和表之间的关系，是业务数据持久化的核心。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

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


# 函数职责：业务函数，封装 权限模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return [item.value for item in enum_cls]


# 类职责：MemberSharePermission 是 权限模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class MemberSharePermission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "member_share_permissions"

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
    # 字段说明：share_all 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    share_all: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # 字段说明：can_view_profile 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    can_view_profile: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # 字段说明：can_view_metrics 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    can_view_metrics: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # 字段说明：can_view_reports 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    can_view_reports: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # 字段说明：can_view_symptoms 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    can_view_symptoms: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # 字段说明：can_view_medical_events 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    can_view_medical_events: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # 字段说明：can_view_documents 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    can_view_documents: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # 字段说明：can_view_alerts 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    can_view_alerts: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # Phase 08.A: alerts:create is now an independent permission for Agent tools
    # and no longer relies on the Phase 07 temporary alerts:view bridge.
    can_create_alerts: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # 字段说明：can_view_memory_summary 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    can_view_memory_summary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # 字段说明：can_create_symptom_records 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    can_create_symptom_records: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # 字段说明：can_create_metric_records 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    can_create_metric_records: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # 字段说明：can_upload_documents 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    can_upload_documents: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # 字段说明：can_create_medical_events 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    can_create_medical_events: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # 字段说明：can_generate_reports 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    can_generate_reports: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # 字段说明：can_generate_doctor_visit_summary 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    can_generate_doctor_visit_summary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # 字段说明：can_export_summary 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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


# 类职责：PermissionAuditLog 是 权限模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, Base。
class PermissionAuditLog(UUIDPrimaryKeyMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "permission_audit_logs"

    # 字段说明：family_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    family_id: Mapped[UUID] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：actor_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    actor_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # 字段说明：target_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    target_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # 字段说明：action 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    action: Mapped[PermissionAuditAction] = mapped_column(
        Enum(
            PermissionAuditAction,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    # 字段说明：permission_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    permission_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：before_snapshot 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    before_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # 字段说明：after_snapshot 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    after_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # 字段说明：reason 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # 字段说明：created_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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
