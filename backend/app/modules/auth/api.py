from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.errors import raise_api_error, raise_unauthorized, ApiErrorCode
from app.core.config import Settings, get_settings
from app.modules.auth import service
from app.modules.auth.api_schemas import (
    AuthLoginRequest,
    AuthLogoutRequest,
    AuthLogoutResponse,
    AuthMeResponse,
    AuthRefreshRequest,
    AuthRegisterRequest,
    AuthTokenResponse,
    auth_token_response,
)
from app.modules.auth.exceptions import AuthConfigurationError, AuthError, AuthUserInactiveError, InvalidCredentialsError, InvalidTokenError


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: AuthRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthTokenResponse:
    try:
        token_pair = service.register_with_password(
            db,
            settings,
            email=payload.email,
            password=payload.password,
            nickname=payload.nickname,
            user_agent=request.headers.get("User-Agent"),
            ip_address=request.client.host if request.client else None,
        )
    except (InvalidCredentialsError, AuthUserInactiveError) as exc:
        raise_unauthorized()
        raise AssertionError("unreachable") from exc
    except AuthConfigurationError as exc:
        raise_api_error(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, code=ApiErrorCode.INTERNAL_SERVER_ERROR)
        raise AssertionError("unreachable") from exc
    return auth_token_response(token_pair)


@router.post("/login", response_model=AuthTokenResponse)
def login(
    payload: AuthLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthTokenResponse:
    try:
        token_pair = service.login_with_password(
            db,
            settings,
            email=payload.email,
            password=payload.password,
            user_agent=request.headers.get("User-Agent"),
            ip_address=request.client.host if request.client else None,
        )
    except (InvalidCredentialsError, AuthUserInactiveError) as exc:
        raise_unauthorized()
        raise AssertionError("unreachable") from exc
    except AuthConfigurationError as exc:
        raise_api_error(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, code=ApiErrorCode.INTERNAL_SERVER_ERROR)
        raise AssertionError("unreachable") from exc
    return auth_token_response(token_pair)


@router.post("/refresh", response_model=AuthTokenResponse)
def refresh(
    payload: AuthRefreshRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthTokenResponse:
    try:
        token_pair = service.refresh_access_token(db, settings, refresh_token=payload.refresh_token)
    except AuthError as exc:
        raise_unauthorized()
        raise AssertionError("unreachable") from exc
    return auth_token_response(token_pair)


@router.post("/logout", response_model=AuthLogoutResponse)
def logout(payload: AuthLogoutRequest, db: Session = Depends(get_db)) -> AuthLogoutResponse:
    try:
        service.logout(db, refresh_token=payload.refresh_token)
    except InvalidTokenError as exc:
        raise_unauthorized()
        raise AssertionError("unreachable") from exc
    return AuthLogoutResponse(status="ok")


@router.get("/me", response_model=AuthMeResponse)
def me(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthMeResponse:
    token = _bearer_token(authorization)
    try:
        auth_user = service.authenticate_access_token(db, settings, token)
    except AuthError as exc:
        raise_unauthorized()
        raise AssertionError("unreachable") from exc
    return AuthMeResponse(
        id=auth_user.user.id,
        email=auth_user.user.email,
        nickname=auth_user.user.nickname,
        session_id=auth_user.session_id,
        authenticated_at=datetime.now(timezone.utc),
    )


def _bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise_unauthorized()
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise_unauthorized()
    token = authorization[len(prefix) :].strip()
    if not token:
        raise_unauthorized()
    return token
