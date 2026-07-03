from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(frozen=True)
class DocumentSafeSummary:
    id: UUID
    user_id: UUID
    document_type: str
    title: str
    file_name: str
    file_mime_type: str | None
    file_size: int | None
    document_date: date | None
    document_date_text: str | None
    hospital_or_org: str | None
    description: str | None
    ai_extract_status: str
    ai_summary: str | None
    extracted_json: dict | None
    confirmed_at: datetime | None
    related_event_count: int
    visibility: str


@dataclass(frozen=True)
class DocumentListSnapshot:
    count: int
    documents: list[DocumentSafeSummary]
