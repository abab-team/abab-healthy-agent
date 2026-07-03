# 模块领域：健康记录模块
# 领域说明：负责症状、用药、就医、备注等事件型健康记录。
# 文件职责：数据模型文件。定义数据库表、字段、索引和表之间的关系，是业务数据持久化的核心。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.health_data.enums import ConfidenceLevel
from app.modules.health_record.enums import (
    HealthRecordDraftStatus,
    HealthRecordDraftType,
    HealthRecordSource,
    SymptomRecordStatus,
)


# 函数职责：业务函数，封装 健康记录模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return [item.value for item in enum_cls]


# 类职责：SymptomRecord 是 健康记录模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class SymptomRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "symptom_records"

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
    # 字段说明：raw_text 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    # 字段说明：symptom_name 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    symptom_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：body_part 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    body_part: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：severity 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 字段说明：started_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # 字段说明：ended_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # 字段说明：duration_text 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    duration_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：occurrence_time_text 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    occurrence_time_text: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    # 字段说明：possible_trigger 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    possible_trigger: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 字段说明：related_metric_types 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    related_metric_types: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    # 字段说明：action_taken 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    action_taken: Mapped[str | None] = mapped_column(String(500), nullable=True)
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
    # 字段说明：status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    status: Mapped[SymptomRecordStatus] = mapped_column(
        Enum(
            SymptomRecordStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=SymptomRecordStatus.ACTIVE,
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
    # 字段说明：ai_summary 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    ai_summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    # 字段说明：timeline_visible 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    timeline_visible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    # 字段说明：source 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    source: Mapped[HealthRecordSource] = mapped_column(
        Enum(
            HealthRecordSource,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=HealthRecordSource.MANUAL,
    )

    __table_args__ = (
        Index("ix_symptom_records_user_id", "user_id"),
        Index("ix_symptom_records_family_id", "family_id"),
        Index("ix_symptom_records_created_by_user_id", "created_by_user_id"),
        Index("ix_symptom_records_symptom_name", "symptom_name"),
        Index("ix_symptom_records_started_at", "started_at"),
        Index("ix_symptom_records_follow_up_needed", "follow_up_needed"),
        Index("ix_symptom_records_status", "status"),
        Index("ix_symptom_records_created_at", "created_at"),
    )


# 类职责：HealthRecordDraft 是 健康记录模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class HealthRecordDraft(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "health_record_drafts"

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
    # 字段说明：target_display_name 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    target_display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    # 字段说明：raw_text 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    # 字段说明：draft_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    draft_type: Mapped[HealthRecordDraftType] = mapped_column(
        Enum(
            HealthRecordDraftType,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    # 字段说明：extracted_json 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    extracted_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    # 字段说明：missing_fields 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    missing_fields: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    # 字段说明：safety_flags 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    safety_flags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
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
    # 字段说明：status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    status: Mapped[HealthRecordDraftStatus] = mapped_column(
        Enum(
            HealthRecordDraftStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=HealthRecordDraftStatus.PENDING,
    )
    # 字段说明：expires_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # 字段说明：confirmed_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # 字段说明：confirmed_record_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    confirmed_record_id: Mapped[UUID | None] = mapped_column(nullable=True)

    __table_args__ = (
        Index("ix_health_record_drafts_user_id", "user_id"),
        Index("ix_health_record_drafts_family_id", "family_id"),
        Index("ix_health_record_drafts_created_by_user_id", "created_by_user_id"),
        Index("ix_health_record_drafts_status", "status"),
        Index("ix_health_record_drafts_expires_at", "expires_at"),
        Index("ix_health_record_drafts_created_at", "created_at"),
    )
