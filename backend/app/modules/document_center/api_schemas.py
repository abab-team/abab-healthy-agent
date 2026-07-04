from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.validators import Description, FileName, FilePath, HospitalOrOrg, ShortText, STRICT_MODEL_CONFIG, Title
from app.modules.document_center.enums import DocumentSource, DocumentType, DocumentVisibility


class DocumentMetadataCreateRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    document_type: DocumentType
    title: Title
    file_name: FileName
    file_path: FilePath
    file_mime_type: ShortText = None
    file_size: int | None = Field(default=None, ge=0)
    document_date: date | None = None
    document_date_text: ShortText = None
    hospital_or_org: HospitalOrOrg = None
    description: Description = None
    visibility: DocumentVisibility = DocumentVisibility.PRIVATE
    source: DocumentSource = DocumentSource.UPLOAD


class DocumentVersionCreateRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    file_name: FileName
    file_path: FilePath
    file_mime_type: ShortText = None
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
