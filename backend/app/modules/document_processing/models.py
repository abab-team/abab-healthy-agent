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


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class DocumentProcessingJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_processing_jobs"

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("medical_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    job_type: Mapped[DocumentProcessingJobType] = mapped_column(
        Enum(
            DocumentProcessingJobType,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
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
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
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


class DocumentExtractionResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_extraction_results"

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("medical_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    processing_job_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("document_processing_jobs.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
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
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_findings: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    doctor_advice: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_events: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    raw_extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    safety_notes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
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


class MedicalEventDraft(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "medical_event_drafts"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("medical_documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    extraction_result_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("document_extraction_results.id", ondelete="SET NULL"),
        nullable=True,
    )
    draft_event_type: Mapped[MedicalEventType] = mapped_column(
        Enum(
            MedicalEventType,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    draft_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    draft_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    missing_fields: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
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
    safety_flags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
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
    confirmed_event_id: Mapped[UUID | None] = mapped_column(nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
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
