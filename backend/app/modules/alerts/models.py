# 模块领域：提醒模块
# 领域说明：负责提醒规则、提醒调度、状态流转和通知触发。
# 文件职责：数据模型文件。定义数据库表、字段、索引和表之间的关系，是业务数据持久化的核心。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

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


# 函数职责：业务函数，封装 提醒模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return [item.value for item in enum_cls]


# 类职责：Alert 是 提醒模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class Alert(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "alerts"

    # 字段说明：user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：family_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：created_by_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：alert_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    alert_type: Mapped[AlertType] = mapped_column(
        Enum(
            AlertType,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    # 字段说明：level 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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
    # 字段说明：title 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # 字段说明：message 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # 字段说明：suggested_action 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    suggested_action: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # 字段说明：related_entity_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    related_entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：related_entity_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    related_entity_id: Mapped[UUID | None] = mapped_column(nullable=True)
    # 字段说明：trigger_reason 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    trigger_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 字段说明：status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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
    # 字段说明：due_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # 字段说明：resolved_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # 字段说明：source 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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


# 类职责：AlertEvent 是 提醒模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, Base。
class AlertEvent(UUIDPrimaryKeyMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "alert_events"

    # 字段说明：alert_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    alert_id: Mapped[UUID] = mapped_column(
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：actor_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：event_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    event_type: Mapped[AlertEventType] = mapped_column(
        Enum(
            AlertEventType,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    # 字段说明：before_status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    before_status: Mapped[AlertStatus | None] = mapped_column(
        Enum(
            AlertStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=True,
    )
    # 字段说明：after_status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    after_status: Mapped[AlertStatus | None] = mapped_column(
        Enum(
            AlertStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=True,
    )
    # 字段说明：note 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 字段说明：created_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
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
