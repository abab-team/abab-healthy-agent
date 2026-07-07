from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import BACKEND_DIR, PROJECT_ROOT, Settings


class DocumentUploadError(ValueError):
    pass


@dataclass(frozen=True)
class StoredDocumentFile:
    file_name: str
    storage_key: str
    mime_type: str
    size_bytes: int


_EXTENSION_BY_MIME = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
}
_SAFE_NAME_PATTERN = re.compile(r"[^A-Za-z0-9._\-\u4e00-\u9fff]+")
_DANGEROUS_EXTENSIONS = {
    ".bat",
    ".cmd",
    ".com",
    ".dll",
    ".exe",
    ".js",
    ".msi",
    ".ps1",
    ".rar",
    ".sh",
    ".tar",
    ".vbs",
    ".zip",
}


def store_uploaded_document(file: UploadFile, settings: Settings) -> StoredDocumentFile:
    if not settings.DOCUMENT_UPLOAD_ENABLED:
        raise DocumentUploadError("document upload is disabled")
    if settings.DOCUMENT_STORAGE_BACKEND != "local":
        raise DocumentUploadError("only local document storage is available in this phase")

    mime_type = (file.content_type or "").lower()
    allowed_mime_types = settings.document_allowed_mime_types
    if mime_type not in allowed_mime_types or mime_type not in _EXTENSION_BY_MIME:
        raise DocumentUploadError("unsupported document file type")

    display_name = sanitize_upload_filename(file.filename or "document")
    _reject_dangerous_extension(display_name)
    storage_root = _storage_root(settings)
    storage_root.mkdir(parents=True, exist_ok=True)

    extension = _EXTENSION_BY_MIME[mime_type]
    storage_key = f"documents/{uuid4().hex}{extension}"
    target_path = (storage_root / Path(storage_key).name).resolve()
    _assert_inside(target_path, storage_root)

    max_bytes = settings.DOCUMENT_MAX_UPLOAD_MB * 1024 * 1024
    size_bytes = _copy_limited(file, target_path, max_bytes=max_bytes)
    return StoredDocumentFile(
        file_name=display_name,
        storage_key=storage_key,
        mime_type=mime_type,
        size_bytes=size_bytes,
    )


def store_document_bytes(
    *,
    content: bytes,
    filename: str,
    mime_type: str,
    settings: Settings,
) -> StoredDocumentFile:
    if not settings.DOCUMENT_UPLOAD_ENABLED:
        raise DocumentUploadError("document upload is disabled")
    if settings.DOCUMENT_STORAGE_BACKEND != "local":
        raise DocumentUploadError("only local document storage is available in this phase")
    normalized_mime_type = (mime_type or "").lower()
    if normalized_mime_type not in settings.document_allowed_mime_types or normalized_mime_type not in _EXTENSION_BY_MIME:
        raise DocumentUploadError("unsupported document file type")
    display_name = sanitize_upload_filename(filename)
    _reject_dangerous_extension(display_name)
    if not content:
        raise DocumentUploadError("document file is empty")
    max_bytes = settings.DOCUMENT_MAX_UPLOAD_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise DocumentUploadError("document file is too large")
    storage_root = _storage_root(settings)
    storage_root.mkdir(parents=True, exist_ok=True)
    storage_key = f"documents/{uuid4().hex}{_EXTENSION_BY_MIME[normalized_mime_type]}"
    target_path = (storage_root / Path(storage_key).name).resolve()
    _assert_inside(target_path, storage_root)
    try:
        target_path.write_bytes(content)
    except Exception:
        if target_path.exists():
            target_path.unlink()
        raise
    return StoredDocumentFile(
        file_name=display_name,
        storage_key=storage_key,
        mime_type=normalized_mime_type,
        size_bytes=len(content),
    )


def delete_stored_document(storage_key: str, settings: Settings) -> None:
    if not storage_key.startswith("documents/"):
        return
    storage_root = _storage_root(settings)
    target_path = (storage_root / Path(storage_key).name).resolve()
    if not _is_inside(target_path, storage_root):
        return
    if target_path.exists():
        target_path.unlink()


def sanitize_upload_filename(filename: str) -> str:
    raw_name = Path(filename.replace("\\", "/")).name.strip()
    if not raw_name or raw_name in {".", ".."}:
        raw_name = "document"
    safe_name = _SAFE_NAME_PATTERN.sub("_", raw_name).strip("._ ")
    if not safe_name:
        safe_name = "document"
    if len(safe_name) > 120:
        stem = Path(safe_name).stem[:100]
        suffix = Path(safe_name).suffix[:16]
        safe_name = f"{stem}{suffix}"
    return safe_name


def _storage_root(settings: Settings) -> Path:
    configured = Path(settings.DOCUMENT_STORAGE_DIR)
    if not configured.is_absolute():
        if configured.parts and configured.parts[0] == "backend":
            configured = PROJECT_ROOT / configured
        else:
            configured = BACKEND_DIR / configured
    return configured.resolve()


def _copy_limited(file: UploadFile, target_path: Path, *, max_bytes: int) -> int:
    size_bytes = 0
    try:
        with target_path.open("wb") as output:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                size_bytes += len(chunk)
                if size_bytes > max_bytes:
                    raise DocumentUploadError("document file is too large")
                output.write(chunk)
    except Exception:
        if target_path.exists():
            target_path.unlink()
        raise
    finally:
        try:
            file.file.seek(0)
        except Exception:
            pass
    if size_bytes <= 0:
        if target_path.exists():
            target_path.unlink()
        raise DocumentUploadError("document file is empty")
    return size_bytes


def _reject_dangerous_extension(filename: str) -> None:
    suffixes = {suffix.lower() for suffix in Path(filename).suffixes}
    if suffixes & _DANGEROUS_EXTENSIONS:
        raise DocumentUploadError("unsupported document file type")


def _assert_inside(path: Path, root: Path) -> None:
    if not _is_inside(path, root):
        raise DocumentUploadError("invalid document storage path")


def _is_inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
