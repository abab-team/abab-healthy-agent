# 模块领域：健康资料中心
# 领域说明：负责体检报告、化验单、处方等文件的元数据、权限和存储引用。
# 文件职责：数据模型文件。定义数据库表、字段、索引和表之间的关系，是业务数据持久化的核心。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utc_now
from app.modules.document_center.enums import (
    DocumentExtractStatus,
    DocumentSource,
    DocumentType,
    DocumentVisibility,
)


# 函数职责：业务函数，封装 健康资料中心 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return [item.value for item in enum_cls]


# 类职责：MedicalDocument 是 健康资料中心 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class MedicalDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "medical_documents"

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
    # 字段说明：uploaded_by_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    uploaded_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # 字段说明：document_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(
            DocumentType,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    # 字段说明：title 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # 字段说明：file_name 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # 字段说明：file_path 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    # 字段说明：file_mime_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    file_mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：file_size 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 字段说明：document_date 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    document_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # 字段说明：document_date_text 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    document_date_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：hospital_or_org 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    hospital_or_org: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # 字段说明：description 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 字段说明：ai_extract_status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    ai_extract_status: Mapped[DocumentExtractStatus] = mapped_column(
        Enum(
            DocumentExtractStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=DocumentExtractStatus.NOT_STARTED,
    )
    # 字段说明：ai_summary 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 字段说明：extracted_json 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    extracted_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # 字段说明：confirmed_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # 字段说明：related_event_count 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    related_event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 字段说明：source 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    source: Mapped[DocumentSource] = mapped_column(
        Enum(
            DocumentSource,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=DocumentSource.UPLOAD,
    )
    # 字段说明：visibility 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    visibility: Mapped[DocumentVisibility] = mapped_column(
        Enum(
            DocumentVisibility,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=DocumentVisibility.PRIVATE,
    )

    __table_args__ = (
        Index("ix_medical_documents_user_id", "user_id"),
        Index("ix_medical_documents_family_id", "family_id"),
        Index("ix_medical_documents_uploaded_by_user_id", "uploaded_by_user_id"),
        Index("ix_medical_documents_document_type", "document_type"),
        Index("ix_medical_documents_document_date", "document_date"),
        Index("ix_medical_documents_ai_extract_status", "ai_extract_status"),
        Index("ix_medical_documents_visibility", "visibility"),
        Index("ix_medical_documents_created_at", "created_at"),
    )


# 类职责：DocumentVersion 是 健康资料中心 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, Base。
class DocumentVersion(UUIDPrimaryKeyMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "document_versions"

    # 字段说明：document_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("medical_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：version_no 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    # 字段说明：file_name 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # 字段说明：file_path 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    # 字段说明：file_mime_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    file_mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：file_size 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 字段说明：created_by_user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # 字段说明：created_at 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_document_versions_document_id", "document_id"),
        Index("ix_document_versions_created_by_user_id", "created_by_user_id"),
        Index("ix_document_versions_created_at", "created_at"),
        Index(
            "uq_document_versions_document_id_version_no",
            "document_id",
            "version_no",
            unique=True,
        ),
    )
