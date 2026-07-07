from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class RagSourceType(StrEnum):
    HEALTH_PROFILE_SUMMARY = "health_profile_summary"
    BLOOD_PRESSURE_SUMMARY = "blood_pressure_summary"
    SYMPTOM_RECORD_SUMMARY = "symptom_record_summary"
    MEDICAL_EVENT_SUMMARY = "medical_event_summary"
    MEDICAL_EVENT_DRAFT_SUMMARY = "medical_event_draft_summary"
    MEDICAL_DOCUMENT_METADATA = "medical_document_metadata"
    DOCUMENT_EXTRACTION_PREVIEW = "document_extraction_preview"
    OCR_EXTRACTION_PREVIEW = "ocr_extraction_preview"
    DAILY_REPORT_SUMMARY = "daily_report_summary"
    ALERT_SUMMARY = "alert_summary"
    AGENT_GENERATED_BRIEF_SUMMARY = "agent_generated_brief_summary"


@dataclass(frozen=True)
class RagIndexRecord:
    record_id: str
    source_type: RagSourceType
    source_id: UUID
    owner_user_id: UUID
    target_user_id: UUID
    family_id: UUID | None
    title: str
    summary_text: str
    safe_excerpt: str
    permission_type: str
    permission_action: str = "view"
    source_created_at: datetime | None = None
    tags: tuple[str, ...] = ()
    metadata_safe: dict[str, str | int | float | bool | None] = field(default_factory=dict)

    @property
    def citation(self) -> str:
        return f"{self.source_type.value}:{self.source_id}"


@dataclass(frozen=True)
class RagChunk:
    chunk_id: str
    record_id: str
    source_type: RagSourceType
    source_id: UUID
    owner_user_id: UUID
    target_user_id: UUID
    family_id: UUID | None
    title: str
    text: str
    safe_excerpt: str
    citation: str
    permission_type: str
    permission_action: str
    source_created_at: datetime | None = None
    tags: tuple[str, ...] = ()
    metadata_safe: dict[str, str | int | float | bool | None] = field(default_factory=dict)


@dataclass(frozen=True)
class RagRetrievedSource:
    source_type: str
    source_id: str
    title: str
    safe_excerpt: str
    citation: str
    score: float
    permission_type: str
    metadata: dict[str, str | int | float | bool | None] = field(default_factory=dict)


@dataclass(frozen=True)
class RagSearchResult:
    query: str
    target_user_id: UUID
    family_id: UUID | None
    results: tuple[RagRetrievedSource, ...]
    rag_enabled: bool
    fallback_reason: str | None = None
