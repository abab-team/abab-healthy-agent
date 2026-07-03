from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.document_center.enums import (
    DocumentExtractStatus,
    DocumentSource,
    DocumentType,
    DocumentVisibility,
)
from app.modules.document_center.models import DocumentVersion, MedicalDocument


def create_medical_document(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID | None = None,
    uploaded_by_user_id: UUID,
    document_type: DocumentType,
    title: str,
    file_name: str,
    file_path: str,
    file_mime_type: str | None = None,
    file_size: int | None = None,
    document_date: date | None = None,
    document_date_text: str | None = None,
    hospital_or_org: str | None = None,
    description: str | None = None,
    ai_extract_status: DocumentExtractStatus = DocumentExtractStatus.NOT_STARTED,
    ai_summary: str | None = None,
    extracted_json: dict | None = None,
    confirmed_at: datetime | None = None,
    related_event_count: int = 0,
    source: DocumentSource = DocumentSource.UPLOAD,
    visibility: DocumentVisibility = DocumentVisibility.PRIVATE,
) -> MedicalDocument:
    document = MedicalDocument(
        user_id=user_id,
        family_id=family_id,
        uploaded_by_user_id=uploaded_by_user_id,
        document_type=document_type,
        title=title,
        file_name=file_name,
        file_path=file_path,
        file_mime_type=file_mime_type,
        file_size=file_size,
        document_date=document_date,
        document_date_text=document_date_text,
        hospital_or_org=hospital_or_org,
        description=description,
        ai_extract_status=ai_extract_status,
        ai_summary=ai_summary,
        extracted_json=extracted_json,
        confirmed_at=confirmed_at,
        related_event_count=related_event_count,
        source=source,
        visibility=visibility,
    )
    db.add(document)
    db.flush()
    return document


def get_medical_document(db: Session, document_id: UUID) -> MedicalDocument | None:
    return db.get(MedicalDocument, document_id)


def list_medical_documents(
    db: Session,
    user_id: UUID,
    *,
    document_type: DocumentType | None = None,
    visibility: DocumentVisibility | None = None,
    limit: int = 100,
) -> list[MedicalDocument]:
    stmt = select(MedicalDocument).where(MedicalDocument.user_id == user_id)
    if document_type is not None:
        stmt = stmt.where(MedicalDocument.document_type == document_type)
    if visibility is not None:
        stmt = stmt.where(MedicalDocument.visibility == visibility)
    return list(db.scalars(stmt.order_by(MedicalDocument.created_at.desc()).limit(limit)))


def update_medical_document(
    db: Session,
    document_id: UUID,
    **fields,
) -> MedicalDocument | None:
    document = get_medical_document(db, document_id)
    if document is None:
        return None
    for key, value in fields.items():
        setattr(document, key, value)
    db.flush()
    return document


def update_extract_status(
    db: Session,
    document_id: UUID,
    status: DocumentExtractStatus,
    *,
    ai_summary: str | None = None,
    extracted_json: dict | None = None,
    confirmed_at: datetime | None = None,
) -> MedicalDocument | None:
    fields = {"ai_extract_status": status}
    if ai_summary is not None:
        fields["ai_summary"] = ai_summary
    if extracted_json is not None:
        fields["extracted_json"] = extracted_json
    if confirmed_at is not None:
        fields["confirmed_at"] = confirmed_at
    return update_medical_document(db, document_id, **fields)


def increment_related_event_count(
    db: Session,
    document_id: UUID,
    *,
    count: int = 1,
) -> MedicalDocument | None:
    document = get_medical_document(db, document_id)
    if document is None:
        return None
    document.related_event_count += count
    db.flush()
    return document


def create_document_version(
    db: Session,
    *,
    document_id: UUID,
    version_no: int,
    file_name: str,
    file_path: str,
    file_mime_type: str | None = None,
    file_size: int | None = None,
    created_by_user_id: UUID,
) -> DocumentVersion:
    version = DocumentVersion(
        document_id=document_id,
        version_no=version_no,
        file_name=file_name,
        file_path=file_path,
        file_mime_type=file_mime_type,
        file_size=file_size,
        created_by_user_id=created_by_user_id,
    )
    db.add(version)
    db.flush()
    return version


def list_document_versions(db: Session, document_id: UUID) -> list[DocumentVersion]:
    stmt = (
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_no.desc())
    )
    return list(db.scalars(stmt))


def get_latest_document_version(
    db: Session,
    document_id: UUID,
) -> DocumentVersion | None:
    stmt = (
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_no.desc())
        .limit(1)
    )
    return db.scalar(stmt)
