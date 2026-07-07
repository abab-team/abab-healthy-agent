from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.modules.auth import repository
from app.modules.auth.exceptions import AuthConfigurationError, AuthUserInactiveError, InvalidCredentialsError, InvalidTokenError
from app.modules.auth.password import hash_password, hash_token, verify_password
from app.modules.auth.schemas import AuthenticatedUser, AuthTokenPair
from app.modules.auth.token import create_access_token, decode_access_token
from app.modules.identity import repository as identity_repository
from app.modules.identity.enums import UserStatus
from app.modules.identity.models import User
from app.modules.identity.schemas import to_user_public


def register_with_password(
    db: Session,
    settings: Settings,
    *,
    email: str,
    password: str,
    nickname: str | None = None,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> AuthTokenPair:
    existing_user = repository.get_user_by_email(db, email)
    if existing_user is not None:
        raise InvalidCredentialsError("invalid credentials")
    user = identity_repository.create_user(
        db,
        email=email,
        nickname=nickname,
        password_hash=hash_password(password),
        status=UserStatus.ACTIVE,
    )
    return _issue_token_pair(db, settings, user=user, user_agent=user_agent, ip_address=ip_address)


def login_with_password(
    db: Session,
    settings: Settings,
    *,
    email: str,
    password: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> AuthTokenPair:
    user = repository.get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("invalid credentials")
    _ensure_active_user(user)
    user.last_login_at = datetime.now(timezone.utc)
    return _issue_token_pair(db, settings, user=user, user_agent=user_agent, ip_address=ip_address)


def refresh_access_token(
    db: Session,
    settings: Settings,
    *,
    refresh_token: str,
) -> AuthTokenPair:
    now = datetime.now(timezone.utc)
    stored_token = repository.get_refresh_token_by_hash(db, hash_token(refresh_token))
    if stored_token is None or stored_token.revoked_at is not None or _is_expired(stored_token.expires_at, now):
        raise InvalidTokenError("invalid token")
    user = repository.get_user_by_id(db, stored_token.user_id)
    if user is None:
        raise InvalidTokenError("invalid token")
    _ensure_active_user(user)
    repository.revoke_refresh_token(db, stored_token, now)
    return _issue_token_pair(db, settings, user=user)


def logout(db: Session, *, refresh_token: str) -> None:
    now = datetime.now(timezone.utc)
    stored_token = repository.get_refresh_token_by_hash(db, hash_token(refresh_token))
    if stored_token is None or stored_token.revoked_at is not None:
        raise InvalidTokenError("invalid token")
    repository.revoke_refresh_token(db, stored_token, now)


def authenticate_access_token(db: Session, settings: Settings, access_token: str) -> AuthenticatedUser:
    payload = decode_access_token(settings, access_token)
    user_id = UUID(str(payload["sub"]))
    session_id = UUID(str(payload["sid"]))
    now = datetime.now(timezone.utc)
    session = repository.get_login_session(db, session_id)
    if session is None or session.user_id != user_id or session.revoked_at is not None or _is_expired(session.expires_at, now):
        raise InvalidTokenError("invalid token")
    user = repository.get_user_by_id(db, user_id)
    if user is None:
        raise InvalidTokenError("invalid token")
    _ensure_active_user(user)
    return AuthenticatedUser(user=to_user_public(user), session_id=session.id)


def _issue_token_pair(
    db: Session,
    settings: Settings,
    *,
    user: User,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> AuthTokenPair:
    _ensure_secret_configured(settings)
    now = datetime.now(timezone.utc)
    session_secret = secrets.token_urlsafe(32)
    session_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    session = repository.create_login_session(
        db,
        user_id=user.id,
        session_token_hash=hash_token(session_secret),
        expires_at=session_expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    refresh_token = secrets.token_urlsafe(48)
    repository.create_refresh_token(
        db,
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    access_token, access_expires_at = create_access_token(settings, user_id=user.id, session_id=session.id, now=now)
    return AuthTokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=to_user_public(user),
        access_expires_at=access_expires_at,
    )


def _ensure_active_user(user: User) -> None:
    if user.status != UserStatus.ACTIVE:
        raise AuthUserInactiveError("inactive user")


def _ensure_secret_configured(settings: Settings) -> None:
    if not (settings.JWT_SECRET_KEY or settings.SECRET_KEY):
        raise AuthConfigurationError("jwt secret is not configured")


def _is_expired(expires_at: datetime, now: datetime) -> bool:
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return expires_at <= now
