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


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class MedicalDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "medical_documents"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    uploaded_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(
            DocumentType,
            values_callable=enum_values,
            native_enum=False,
            length=64,
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    document_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    document_date_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hospital_or_org: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    related_event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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


class DocumentVersion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "document_versions"

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("medical_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
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
