from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.document_center.enums import DocumentSource, DocumentType, DocumentVisibility


class DocumentMetadataCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: DocumentType
    title: str = Field(min_length=1, max_length=200)
    file_name: str = Field(min_length=1, max_length=255)
    file_path: str = Field(min_length=1, max_length=500)
    file_mime_type: str | None = Field(default=None, max_length=100)
    file_size: int | None = Field(default=None, ge=0)
    document_date: date | None = None
    document_date_text: str | None = Field(default=None, max_length=100)
    hospital_or_org: str | None = Field(default=None, max_length=200)
    description: str | None = None
    visibility: DocumentVisibility = DocumentVisibility.PRIVATE
    source: DocumentSource = DocumentSource.UPLOAD


class DocumentVersionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_name: str = Field(min_length=1, max_length=255)
    file_path: str = Field(min_length=1, max_length=500)
    file_mime_type: str | None = Field(default=None, max_length=100)
    file_size: int | None = Field(default=None, ge=0)


class DocumentSafeResponse(BaseModel):
    id: UUID
    user_id: UUID
    family_id: UUID | None = None
    uploaded_by_user_id: UUID | None = None
    document_type: str
    title: str
    file_name: str
    file_mime_type: str | None = None
    file_size: int | None = None
    document_date: date | None = None
    document_date_text: str | None = None
    hospital_or_org: str | None = None
    description: str | None = None
    ai_extract_status: str
    ai_summary: str | None = None
    extracted_json: dict | None = None
    confirmed_at: datetime | None = None
    related_event_count: int
    visibility: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DocumentVersionResponse(BaseModel):
    id: UUID
    document_id: UUID
    version_no: int
    file_name: str
    file_mime_type: str | None = None
    file_size: int | None = None
    created_by_user_id: UUID
    created_at: datetime
