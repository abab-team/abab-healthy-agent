# 模块领域：医疗时间线模块
# 领域说明：负责过敏、用药、手术、随访等长期医疗事件串联。
# 文件职责：数据模型文件。定义数据库表、字段、索引和表之间的关系，是业务数据持久化的核心。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.health_data.enums import ConfidenceLevel
from app.modules.medical_timeline.enums import (
    MedicalEventSource,
    MedicalEventStatus,
    MedicalEventType,
)


# 函数职责：业务函数，封装 医疗时间线模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return [item.value for item in enum_cls]


# 类职责：MedicalEvent 是 医疗时间线模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class MedicalEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "medical_events"

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
    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # 字段说明：event_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    event_type: Mapped[MedicalEventType] = mapped_column(
        Enum(
            MedicalEventType,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    # 字段说明：title 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # 字段说明：event_date 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # 字段说明：event_date_text 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    event_date_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：hospital_or_org 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    hospital_or_org: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # 字段说明：department 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：diagnosis_text 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    diagnosis_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # 字段说明：summary 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 字段说明：doctor_advice 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    doctor_advice: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 字段说明：medications 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    medications: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    # 字段说明：key_findings 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    key_findings: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    # 字段说明：follow_up_needed 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    follow_up_needed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # 字段说明：follow_up_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    follow_up_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # 字段说明：related_document_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    related_document_id: Mapped[UUID | None] = mapped_column(nullable=True)
    # 字段说明：source 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    source: Mapped[MedicalEventSource] = mapped_column(
        Enum(
            MedicalEventSource,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=MedicalEventSource.MANUAL,
    )
    # 字段说明：confidence_level 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    confidence_level: Mapped[ConfidenceLevel] = mapped_column(
        Enum(
            ConfidenceLevel,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=ConfidenceLevel.UNKNOWN,
    )
    # 字段说明：timeline_visible 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    timeline_visible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    # 字段说明：status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    status: Mapped[MedicalEventStatus] = mapped_column(
        Enum(
            MedicalEventStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=MedicalEventStatus.ACTIVE,
    )

    __table_args__ = (
        Index("ix_medical_events_user_id", "user_id"),
        Index("ix_medical_events_family_id", "family_id"),
        Index("ix_medical_events_created_by_user_id", "created_by_user_id"),
        Index("ix_medical_events_event_type", "event_type"),
        Index("ix_medical_events_event_date", "event_date"),
        Index("ix_medical_events_follow_up_needed", "follow_up_needed"),
        Index("ix_medical_events_follow_up_at", "follow_up_at"),
        Index("ix_medical_events_status", "status"),
        Index("ix_medical_events_related_document_id", "related_document_id"),
        Index("ix_medical_events_created_at", "created_at"),
    )
