from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.document_processing.enums import (
    DocumentExtractionMode,
    DocumentExtractionResultStatus,
    DocumentProcessingJobType,
)
from app.modules.health_data.enums import ConfidenceLevel
from app.modules.medical_timeline.enums import MedicalEventType


class ProcessingJobCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_type: DocumentProcessingJobType = DocumentProcessingJobType.AI_EXTRACT


class ProcessingJobFailedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error_message: str = Field(min_length=1, max_length=1000)


class ProcessingJobResponse(BaseModel):
    id: UUID
    document_id: UUID
    user_id: UUID
    family_id: UUID | None = None
    job_type: str
    status: str
    attempt_count: int
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ExtractionResultCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extraction_mode: DocumentExtractionMode = DocumentExtractionMode.STANDARD
    ai_summary: str | None = None
    key_findings: list[dict] | None = None
    doctor_advice: str | None = None
    suggested_events: list[dict] | None = None
    raw_extracted_text: str | None = None
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    safety_notes: list[str] | None = None
    status: DocumentExtractionResultStatus = DocumentExtractionResultStatus.DRAFT
    processing_job_id: UUID | None = None


class ExtractionResultResponse(BaseModel):
    id: UUID
    document_id: UUID
    processing_job_id: UUID | None = None
    user_id: UUID
    family_id: UUID | None = None
    extraction_mode: str
    ai_summary: str | None = None
    key_findings: list[dict] | None = None
    doctor_advice: str | None = None
    suggested_events: list[dict] | None = None
    confidence_level: str
    safety_notes: list[str] | None = None
    status: str
    raw_text_excerpt: str | None = None
    created_at: datetime
    updated_at: datetime


class MedicalEventDraftCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_document_id: UUID | None = None
    extraction_result_id: UUID | None = None
    draft_event_type: MedicalEventType
    draft_title: str | None = Field(default=None, max_length=200)
    draft_json: dict
    missing_fields: list[str] | None = None
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    safety_flags: list[str] | None = None
    expires_at: datetime | None = None


class MedicalEventDraftResponse(BaseModel):
    id: UUID
    user_id: UUID
    family_id: UUID | None = None
    created_by_user_id: UUID
    source_document_id: UUID | None = None
    extraction_result_id: UUID | None = None
    draft_event_type: str
    draft_title: str | None = None
    draft_json: dict
    missing_fields: list[str] | None = None
    confidence_level: str
    safety_flags: list[str] | None = None
    status: str
    confirmed_event_id: UUID | None = None
    confirmed_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
