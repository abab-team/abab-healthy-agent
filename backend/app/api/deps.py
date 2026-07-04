from __future__ import annotations

from collections.abc import Generator
from uuid import UUID

from fastapi import Header
from sqlalchemy.orm import Session

from app.api.errors import ApiErrorCode, raise_bad_request, raise_unauthorized
from app.db.session import SessionLocal


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


def get_current_user_id_for_demo(
    x_current_user_id: str | None = Header(default=None, alias="X-Current-User-Id"),
) -> UUID:
    # Temporary demo authentication. A later auth phase will replace this
    # header with the real authentication/JWT context.
    if not x_current_user_id:
        raise_unauthorized(code=ApiErrorCode.MISSING_CURRENT_USER)
    try:
        return UUID(x_current_user_id)
    except ValueError as exc:
        raise_bad_request("X-Current-User-Id must be a valid UUID.")
        raise AssertionError("unreachable") from exc
