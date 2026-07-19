from __future__ import annotations

from pathlib import Path
from uuid import UUID

from app.core.config import Settings


class AvatarUploadError(ValueError):
    pass


_MIME_SUFFIXES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
_MAX_AVATAR_BYTES = 5 * 1024 * 1024


def store_avatar_bytes(*, content: bytes, mime_type: str | None, user_id: UUID, settings: Settings) -> None:
    normalized_mime_type = (mime_type or "").split(";", 1)[0].strip().lower()
    suffix = _MIME_SUFFIXES.get(normalized_mime_type)
    if suffix is None:
        raise AvatarUploadError("only JPEG, PNG, and WebP images can be used as avatars")
    if not content:
        raise AvatarUploadError("avatar image cannot be empty")
    if len(content) > _MAX_AVATAR_BYTES:
        raise AvatarUploadError("avatar image must be 5 MB or smaller")

    folder = Path(settings.LOCAL_STORAGE_DIR).resolve() / "avatars" / str(user_id)
    folder.mkdir(parents=True, exist_ok=True)
    for existing in folder.glob("avatar.*"):
        existing.unlink(missing_ok=True)
    file_path = folder / f"avatar{suffix}"
    file_path.write_bytes(content)


def get_avatar_path(*, user_id: UUID, settings: Settings) -> Path:
    folder = Path(settings.LOCAL_STORAGE_DIR).resolve() / "avatars" / str(user_id)
    candidates = list(folder.glob("avatar.*"))
    if len(candidates) != 1:
        raise AvatarUploadError("avatar not found")
    path = candidates[0].resolve()
    if not path.is_file():
        raise AvatarUploadError("avatar not found")
    return path
