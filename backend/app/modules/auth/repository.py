from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.identity.models import LoginSession, RefreshToken, User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.get(User, user_id)


def create_login_session(
    db: Session,
    *,
    user_id: UUID,
    session_token_hash: str,
    expires_at: datetime,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> LoginSession:
    session = LoginSession(
        user_id=user_id,
        session_token_hash=session_token_hash,
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=expires_at,
    )
    db.add(session)
    db.flush()
    return session


def get_login_session(db: Session, session_id: UUID) -> LoginSession | None:
    return db.get(LoginSession, session_id)


def create_refresh_token(
    db: Session,
    *,
    user_id: UUID,
    token_hash: str,
    expires_at: datetime,
) -> RefreshToken:
    refresh_token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    db.add(refresh_token)
    db.flush()
    return refresh_token


def get_refresh_token_by_hash(db: Session, token_hash: str) -> RefreshToken | None:
    return db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))


def revoke_refresh_token(db: Session, refresh_token: RefreshToken, revoked_at: datetime) -> None:
    refresh_token.revoked_at = revoked_at
    db.flush()


def revoke_login_session(db: Session, session: LoginSession, revoked_at: datetime) -> None:
    session.revoked_at = revoked_at
    db.flush()
