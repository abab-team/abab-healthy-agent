from __future__ import annotations

from collections.abc import Generator
from uuid import UUID

from fastapi import Header, HTTPException, status
from sqlalchemy.orm import Session

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current phase requires X-Current-User-Id header.",
        )
    try:
        return UUID(x_current_user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Current-User-Id must be a valid UUID.",
        ) from exc
