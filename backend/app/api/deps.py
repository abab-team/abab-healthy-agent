from __future__ import annotations

from collections.abc import Generator
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.api.errors import ApiErrorCode, raise_bad_request, raise_unauthorized
from app.core.config import Settings, get_settings
from app.db.session import SessionLocal
from app.modules.auth import service as auth_service
from app.modules.auth.exceptions import AuthError


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_current_user_id(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_current_user_id: str | None = Header(default=None, alias="X-Current-User-Id"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UUID:
    if authorization:
        token = _bearer_token(authorization)
        try:
            auth_user = auth_service.authenticate_access_token(db, settings, token)
        except AuthError as exc:
            raise_unauthorized()
            raise AssertionError("unreachable") from exc
        return auth_user.user.id

    if not settings.AUTH_DEMO_HEADER_ENABLED:
        raise_unauthorized(code=ApiErrorCode.MISSING_CURRENT_USER)

    if not x_current_user_id:
        raise_unauthorized(code=ApiErrorCode.MISSING_CURRENT_USER)
    try:
        return UUID(x_current_user_id)
    except ValueError as exc:
        raise_bad_request("X-Current-User-Id must be a valid UUID.")
        raise AssertionError("unreachable") from exc


def get_current_user_id_for_demo(
    current_user_id: UUID = Depends(get_current_user_id),
) -> UUID:
    return current_user_id


def get_current_user_id_optional(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_current_user_id: str | None = Header(default=None, alias="X-Current-User-Id"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UUID | None:
    if not authorization and not x_current_user_id:
        return None
    return get_current_user_id(authorization, x_current_user_id, db, settings)


def _bearer_token(authorization: str) -> str:
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise_unauthorized()
    token = authorization[len(prefix) :].strip()
    if not token:
        raise_unauthorized()
    return token
