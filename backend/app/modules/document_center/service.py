from __future__ import annotations

from datetime import date, datetime, timezone
from enum import StrEnum
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.document_center import repository
from app.modules.document_center.enums import (
    DocumentExtractStatus,
    DocumentSource,
    DocumentType,
    DocumentVisibility,
)
from app.modules.document_center.exceptions import (
    InvalidDocumentMetadataError,
    MedicalDocumentNotFoundError,
)
from app.modules.document_center.models import DocumentVersion, MedicalDocument
from app.modules.document_center.schemas import DocumentSafeSummary


def create_document_metadata(
    db: Session,
    *,
    user_id: UUID,
    uploaded_by_user_id: UUID,
    document_type: DocumentType | str,
    title: str,
    file_name: str,
    file_path: str,
    family_id: UUID | None = None,
    file_mime_type: str | None = None,
    file_size: int | None = None,
    document_date: date | None = None,
    document_date_text: str | None = None,
    hospital_or_org: str | None = None,
    description: str | None = None,
    source: DocumentSource | str = DocumentSource.UPLOAD,
    visibility: DocumentVisibility | str = DocumentVisibility.PRIVATE,
) -> MedicalDocument:
    _validate_required_text(title, "title")
    _validate_required_text(file_name, "file_name")
    _validate_required_text(file_path, "file_path")
    return repository.create_medical_document(
        db,
        user_id=user_id,
        family_id=family_id,
        uploaded_by_user_id=uploaded_by_user_id,
        document_type=_coerce_enum(DocumentType, document_type),
        title=title.strip(),
        file_name=file_name.strip(),
        file_path=file_path,
        file_mime_type=file_mime_type,
        file_size=file_size,
        document_date=document_date,
        document_date_text=document_date_text,
        hospital_or_org=hospital_or_org,
        description=description,
        source=_coerce_enum(DocumentSource, source),
        visibility=_coerce_enum(DocumentVisibility, visibility),
    )


def get_document(db: Session, document_id: UUID) -> MedicalDocument:
    document = repository.get_medical_document(db, document_id)
    if document is None:
        raise MedicalDocumentNotFoundError("medical document not found")
    return document


def get_document_safe_summary(
    db: Session,
    document_id: UUID,
) -> DocumentSafeSummary:
    return _safe_summary(get_document(db, document_id))


def list_user_documents(
    db: Session,
    *,
    user_id: UUID,
    document_type: DocumentType | str | None = None,
    visibility: DocumentVisibility | str | None = None,
) -> list[MedicalDocument]:
    return repository.list_medical_documents(
        db,
        user_id,
        document_type=_coerce_enum(DocumentType, document_type) if document_type else None,
        visibility=_coerce_enum(DocumentVisibility, visibility) if visibility else None,
    )


def mark_document_processing(db: Session, document_id: UUID) -> MedicalDocument:
    return _update_extract_status(db, document_id, DocumentExtractStatus.PROCESSING)


def mark_document_extract_success(
    db: Session,
    document_id: UUID,
    *,
    ai_summary: str | None = None,
    extracted_json: dict | None = None,
) -> MedicalDocument:
    return _update_extract_status(
        db,
        document_id,
        DocumentExtractStatus.SUCCESS,
        ai_summary=ai_summary,
        extracted_json=extracted_json,
    )


def mark_document_extract_failed(
    db: Session,
    document_id: UUID,
    *,
    error_message: str | None = None,
) -> MedicalDocument:
    return _update_extract_status(
        db,
        document_id,
        DocumentExtractStatus.FAILED,
        ai_summary=error_message,
    )


def mark_document_confirmed(db: Session, document_id: UUID) -> MedicalDocument:
    return _update_extract_status(
        db,
        document_id,
        DocumentExtractStatus.CONFIRMED,
        confirmed_at=datetime.now(timezone.utc),
    )


def add_document_version(
    db: Session,
    document_id: UUID,
    *,
    file_name: str,
    file_path: str,
    file_mime_type: str | None = None,
    file_size: int | None = None,
    created_by_user_id: UUID | None = None,
) -> DocumentVersion:
    document = get_document(db, document_id)
    _validate_required_text(file_name, "file_name")
    _validate_required_text(file_path, "file_path")
    latest = repository.get_latest_document_version(db, document_id)
    version_no = latest.version_no + 1 if latest else 1
    return repository.create_document_version(
        db,
        document_id=document_id,
        version_no=version_no,
        file_name=file_name.strip(),
        file_path=file_path,
        file_mime_type=file_mime_type,
        file_size=file_size,
        created_by_user_id=created_by_user_id or document.uploaded_by_user_id,
    )


def _update_extract_status(
    db: Session,
    document_id: UUID,
    status: DocumentExtractStatus,
    *,
    ai_summary: str | None = None,
    extracted_json: dict | None = None,
    confirmed_at: datetime | None = None,
) -> MedicalDocument:
    document = repository.update_extract_status(
        db,
        document_id,
        status,
        ai_summary=ai_summary,
        extracted_json=extracted_json,
        confirmed_at=confirmed_at,
    )
    if document is None:
        raise MedicalDocumentNotFoundError("medical document not found")
    return document


def _safe_summary(document: MedicalDocument) -> DocumentSafeSummary:
    return DocumentSafeSummary(
        id=document.id,
        user_id=document.user_id,
        document_type=document.document_type.value,
        title=document.title,
        file_name=document.file_name,
        file_mime_type=document.file_mime_type,
        file_size=document.file_size,
        document_date=document.document_date,
        document_date_text=document.document_date_text,
        hospital_or_org=document.hospital_or_org,
        description=document.description,
        ai_extract_status=document.ai_extract_status.value,
        ai_summary=document.ai_summary,
        extracted_json=document.extracted_json,
        confirmed_at=document.confirmed_at,
        related_event_count=document.related_event_count,
        visibility=document.visibility.value,
    )


def _validate_required_text(value: str | None, field_name: str) -> None:
    if not value or not value.strip():
        raise InvalidDocumentMetadataError(f"{field_name} is required")


def _coerce_enum(enum_cls: type[StrEnum], value):
    if isinstance(value, enum_cls):
        return value
    return enum_cls(value)
