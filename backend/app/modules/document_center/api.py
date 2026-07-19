from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.access_control import require_self_or_family_permission
from app.api.deps import get_current_user_id_for_demo, get_db
from app.core.config import Settings, get_settings
from app.modules.document_center import storage
from app.modules.document_center import service
from app.modules.document_center.api_schemas import (
    DocumentMetadataCreateRequest,
    DocumentSafeResponse,
    DocumentVersionCreateRequest,
    DocumentVersionResponse,
)
from app.modules.document_center.enums import DocumentType, DocumentVisibility
from app.modules.document_center.exceptions import InvalidDocumentMetadataError, MedicalDocumentNotFoundError


router = APIRouter(tags=["documents"])


@router.post("/documents/me", response_model=DocumentSafeResponse, status_code=status.HTTP_201_CREATED)
def create_my_document_metadata(
    payload: DocumentMetadataCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    return _create_document(db, user_id=current_user_id, family_id=None, uploaded_by_user_id=current_user_id, payload=payload)


@router.post("/documents/me/upload", response_model=DocumentSafeResponse, status_code=status.HTTP_201_CREATED)
async def upload_my_document(
    request: Request,
    document_type: DocumentType = Query(DocumentType.OTHER),
    title: str | None = Query(None),
    visibility: DocumentVisibility = Query(DocumentVisibility.PRIVATE),
    x_file_name: str | None = Header(None, alias="X-File-Name"),
    content_type: str | None = Header(None, alias="Content-Type"),
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    return _store_and_create_document(
        db,
        content=await request.body(),
        file_name=x_file_name,
        mime_type=content_type,
        settings=settings,
        user_id=current_user_id,
        family_id=None,
        uploaded_by_user_id=current_user_id,
        document_type=document_type,
        title=title,
        visibility=visibility,
    )


@router.get("/documents/me")
def list_my_documents(
    document_type: str | None = None,
    visibility: str | None = None,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    return {"items": [_document_response(doc) for doc in _list_documents(db, current_user_id, document_type, visibility)]}


@router.get("/documents/me/{document_id}", response_model=DocumentSafeResponse)
def get_my_document(
    document_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    document = _get_document_or_404(db, document_id)
    _assert_document_scope(document, user_id=current_user_id, family_id=None)
    return _document_response(document)


@router.get("/documents/me/{document_id}/content")
def get_my_document_content(
    document_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    document = _get_document_or_404(db, document_id)
    _assert_document_scope(document, user_id=current_user_id, family_id=None)
    try:
        file_path = storage.get_stored_document_path(document.file_path, settings)
    except storage.DocumentUploadError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FileResponse(
        file_path,
        filename=document.file_name,
        media_type=document.file_mime_type or "application/octet-stream",
        content_disposition_type="inline",
    )


@router.post("/documents/me/{document_id}/versions", response_model=DocumentVersionResponse, status_code=status.HTTP_201_CREATED)
def add_my_document_version(
    document_id: UUID,
    payload: DocumentVersionCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    document = _get_document_or_404(db, document_id)
    _assert_document_scope(document, user_id=current_user_id, family_id=None)
    try:
        version = service.add_document_version(db, document_id, created_by_user_id=current_user_id, **payload.model_dump())
    except (InvalidDocumentMetadataError, MedicalDocumentNotFoundError) as exc:
        raise _bad_request(exc) from exc
    return _version_response(version)


@router.post("/documents/me/{document_id}/mark-processing", response_model=DocumentSafeResponse)
def mark_my_document_processing(
    document_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    document = _get_document_or_404(db, document_id)
    _assert_document_scope(document, user_id=current_user_id, family_id=None)
    return _document_response(service.mark_document_processing(db, document_id))


@router.post("/documents/me/{document_id}/mark-confirmed", response_model=DocumentSafeResponse)
def mark_my_document_confirmed(
    document_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    document = _get_document_or_404(db, document_id)
    _assert_document_scope(document, user_id=current_user_id, family_id=None)
    return _document_response(service.mark_document_confirmed(db, document_id))


@router.post("/families/{family_id}/members/{target_user_id}/documents", response_model=DocumentSafeResponse, status_code=status.HTTP_201_CREATED)
def create_family_member_document_metadata(
    family_id: UUID,
    target_user_id: UUID,
    payload: DocumentMetadataCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "documents", "create")
    return _create_document(db, user_id=target_user_id, family_id=family_id, uploaded_by_user_id=current_user_id, payload=payload)


@router.post(
    "/families/{family_id}/members/{target_user_id}/documents/upload",
    response_model=DocumentSafeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_family_member_document(
    family_id: UUID,
    target_user_id: UUID,
    request: Request,
    document_type: DocumentType = Query(DocumentType.OTHER),
    title: str | None = Query(None),
    visibility: DocumentVisibility = Query(DocumentVisibility.FAMILY_SHARED),
    x_file_name: str | None = Header(None, alias="X-File-Name"),
    content_type: str | None = Header(None, alias="Content-Type"),
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "documents", "create")
    return _store_and_create_document(
        db,
        content=await request.body(),
        file_name=x_file_name,
        mime_type=content_type,
        settings=settings,
        user_id=target_user_id,
        family_id=family_id,
        uploaded_by_user_id=current_user_id,
        document_type=document_type,
        title=title,
        visibility=visibility,
    )


@router.get("/families/{family_id}/members/{target_user_id}/documents")
def list_family_member_documents(
    family_id: UUID,
    target_user_id: UUID,
    document_type: str | None = None,
    visibility: str | None = None,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "documents", "view")
    return {"items": [_document_response(doc) for doc in _list_family_documents(db, target_user_id, family_id, document_type, visibility)]}


@router.get("/families/{family_id}/members/{target_user_id}/documents/{document_id}", response_model=DocumentSafeResponse)
def get_family_member_document(
    family_id: UUID,
    target_user_id: UUID,
    document_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user_id, family_id, target_user_id, "documents", "view")
    document = _get_document_or_404(db, document_id)
    _assert_document_scope(document, user_id=target_user_id, family_id=family_id)
    return _document_response(document)


def _create_document(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID | None,
    uploaded_by_user_id: UUID,
    payload: DocumentMetadataCreateRequest,
) -> dict:
    try:
        document = service.create_document_metadata(
            db,
            user_id=user_id,
            family_id=family_id,
            uploaded_by_user_id=uploaded_by_user_id,
            **payload.model_dump(),
        )
    except (InvalidDocumentMetadataError, ValueError) as exc:
        raise _bad_request(exc) from exc
    return _document_response(document)


def _store_and_create_document(
    db: Session,
    *,
    content: bytes,
    file_name: str | None,
    mime_type: str | None,
    settings: Settings,
    user_id: UUID,
    family_id: UUID | None,
    uploaded_by_user_id: UUID,
    document_type: DocumentType,
    title: str | None,
    visibility: DocumentVisibility,
) -> dict:
    try:
        stored = storage.store_document_bytes(
            content=content,
            filename=file_name or "document",
            mime_type=mime_type or "",
            settings=settings,
        )
        payload = DocumentMetadataCreateRequest(
            document_type=document_type,
            title=(title or stored.file_name),
            file_name=stored.file_name,
            file_path=stored.storage_key,
            file_mime_type=stored.mime_type,
            file_size=stored.size_bytes,
            visibility=visibility,
        )
        return _create_document(
            db,
            user_id=user_id,
            family_id=family_id,
            uploaded_by_user_id=uploaded_by_user_id,
            payload=payload,
        )
    except storage.DocumentUploadError as exc:
        raise _bad_request(exc) from exc
    except Exception:
        stored_key = locals().get("stored").storage_key if "stored" in locals() else None
        if stored_key:
            storage.delete_stored_document(stored_key, settings)
        raise


def _list_documents(db: Session, user_id: UUID, document_type: str | None, visibility: str | None):
    try:
        return service.list_user_documents(db, user_id=user_id, family_id=None, document_type=document_type, visibility=visibility)
    except ValueError as exc:
        raise _bad_request(exc) from exc


def _list_family_documents(db: Session, user_id: UUID, family_id: UUID, document_type: str | None, visibility: str | None):
    try:
        return service.list_user_documents(db, user_id=user_id, family_id=family_id, document_type=document_type, visibility=visibility)
    except ValueError as exc:
        raise _bad_request(exc) from exc


def _get_document_or_404(db: Session, document_id: UUID):
    try:
        return service.get_document(db, document_id)
    except MedicalDocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def _assert_document_scope(document, *, user_id: UUID, family_id: UUID | None) -> None:
    if document.user_id != user_id or document.family_id != family_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="medical document not found")


def _require_permission(db: Session, current_user_id: UUID, family_id: UUID, target_user_id: UUID, permission_type: str, action: str) -> None:
    require_self_or_family_permission(
        db,
        current_user_id=current_user_id,
        family_id=family_id,
        target_user_id=target_user_id,
        permission_type=permission_type,
        action=action,
        data_category="documents",
        access_reason="api_document_center",
    )


def _document_response(document) -> dict:
    return {
        "id": document.id,
        "user_id": document.user_id,
        "family_id": document.family_id,
        "uploaded_by_user_id": document.uploaded_by_user_id,
        "document_type": _enum_value(document.document_type),
        "title": document.title,
        "file_name": document.file_name,
        "file_mime_type": document.file_mime_type,
        "file_size": document.file_size,
        "document_date": document.document_date,
        "document_date_text": document.document_date_text,
        "hospital_or_org": document.hospital_or_org,
        "description": document.description,
        "ai_extract_status": _enum_value(document.ai_extract_status),
        "ai_summary": document.ai_summary,
        "extracted_json": document.extracted_json,
        "confirmed_at": document.confirmed_at,
        "related_event_count": document.related_event_count,
        "visibility": _enum_value(document.visibility),
        "created_at": document.created_at,
        "updated_at": document.updated_at,
    }


def _version_response(version) -> dict:
    return {
        "id": version.id,
        "document_id": version.document_id,
        "version_no": version.version_no,
        "file_name": version.file_name,
        "file_mime_type": version.file_mime_type,
        "file_size": version.file_size,
        "created_by_user_id": version.created_by_user_id,
        "created_at": version.created_at,
    }


def _enum_value(value):
    return value.value if hasattr(value, "value") else value


def _bad_request(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
