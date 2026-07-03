# 模块领域：文档处理模块
# 领域说明：负责 OCR、信息抽取、人工确认和结构化入库流程。
# 文件职责：数据模型文件。定义数据库表、字段、索引和表之间的关系，是业务数据持久化的核心。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.document_processing.enums import (
    DocumentExtractionMode,
    DocumentExtractionResultStatus,
    DocumentProcessingJobType,
    DocumentProcessingStatus,
    MedicalEventDraftStatus,
)
from app.modules.health_data.enums import ConfidenceLevel
from app.modules.medical_timeline.enums import MedicalEventType


# 函数职责：业务函数，封装 文档处理模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return [item.value for item in enum_cls]


# 类职责：DocumentProcessingJob 是 文档处理模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class DocumentProcessingJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "document_processing_jobs"

    # 字段说明：document_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("medical_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
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
    # 字段说明：job_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    job_type: Mapped[DocumentProcessingJobType] = mapped_column(
        Enum(
            DocumentProcessingJobType,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    # 字段说明：status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    status: Mapped[DocumentProcessingStatus] = mapped_column(
        Enum(
            DocumentProcessingStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=DocumentProcessingStatus.PENDING,
    )
    # 字段说明：attempt_count 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 字段说明：error_message 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 字段说明：started_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # 字段说明：finished_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_document_processing_jobs_document_id", "document_id"),
        Index("ix_document_processing_jobs_user_id", "user_id"),
        Index("ix_document_processing_jobs_family_id", "family_id"),
        Index("ix_document_processing_jobs_job_type", "job_type"),
        Index("ix_document_processing_jobs_status", "status"),
        Index("ix_document_processing_jobs_created_at", "created_at"),
    )


# 类职责：DocumentExtractionResult 是 文档处理模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class DocumentExtractionResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "document_extraction_results"

    # 字段说明：document_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("medical_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：processing_job_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    processing_job_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("document_processing_jobs.id", ondelete="SET NULL"),
        nullable=True,
    )
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
    # 字段说明：extraction_mode 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    extraction_mode: Mapped[DocumentExtractionMode] = mapped_column(
        Enum(
            DocumentExtractionMode,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=DocumentExtractionMode.STANDARD,
    )
    # 字段说明：ai_summary 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 字段说明：key_findings 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    key_findings: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    # 字段说明：doctor_advice 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    doctor_advice: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 字段说明：suggested_events 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    suggested_events: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    # 字段说明：raw_extracted_text 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    raw_extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    # 字段说明：safety_notes 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    safety_notes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    # 字段说明：status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    status: Mapped[DocumentExtractionResultStatus] = mapped_column(
        Enum(
            DocumentExtractionResultStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=DocumentExtractionResultStatus.DRAFT,
    )

    __table_args__ = (
        Index("ix_document_extraction_results_document_id", "document_id"),
        Index("ix_document_extraction_results_processing_job_id", "processing_job_id"),
        Index("ix_document_extraction_results_user_id", "user_id"),
        Index("ix_document_extraction_results_family_id", "family_id"),
        Index("ix_document_extraction_results_status", "status"),
        Index("ix_document_extraction_results_confidence_level", "confidence_level"),
        Index("ix_document_extraction_results_created_at", "created_at"),
    )


# 类职责：MedicalEventDraft 是 文档处理模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class MedicalEventDraft(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "medical_event_drafts"

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
    # 字段说明：source_document_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    source_document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("medical_documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：extraction_result_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    extraction_result_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("document_extraction_results.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：draft_event_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    draft_event_type: Mapped[MedicalEventType] = mapped_column(
        Enum(
            MedicalEventType,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    # 字段说明：draft_title 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    draft_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # 字段说明：draft_json 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    draft_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    # 字段说明：missing_fields 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    missing_fields: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
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
    # 字段说明：safety_flags 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    safety_flags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    # 字段说明：status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    status: Mapped[MedicalEventDraftStatus] = mapped_column(
        Enum(
            MedicalEventDraftStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=MedicalEventDraftStatus.PENDING,
    )
    # 字段说明：confirmed_event_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    confirmed_event_id: Mapped[UUID | None] = mapped_column(nullable=True)
    # 字段说明：confirmed_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # 字段说明：expires_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_medical_event_drafts_user_id", "user_id"),
        Index("ix_medical_event_drafts_family_id", "family_id"),
        Index("ix_medical_event_drafts_created_by_user_id", "created_by_user_id"),
        Index("ix_medical_event_drafts_source_document_id", "source_document_id"),
        Index("ix_medical_event_drafts_extraction_result_id", "extraction_result_id"),
        Index("ix_medical_event_drafts_draft_event_type", "draft_event_type"),
        Index("ix_medical_event_drafts_status", "status"),
        Index("ix_medical_event_drafts_confirmed_event_id", "confirmed_event_id"),
        Index("ix_medical_event_drafts_created_at", "created_at"),
    )
