from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.validators import Email, Nickname, STRICT_MODEL_CONFIG
from app.modules.auth.schemas import AuthTokenPair
from app.modules.identity.api_schemas import UserResponse, user_response


class AuthRegisterRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    email: Email
    password: str = Field(min_length=8, max_length=128)
    nickname: Nickname = None


class AuthLoginRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    email: Email
    password: str = Field(min_length=1, max_length=128)


class AuthRefreshRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    refresh_token: str = Field(min_length=16, max_length=512)


class AuthLogoutRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    refresh_token: str = Field(min_length=16, max_length=512)
    access_token: str | None = Field(default=None, min_length=16, max_length=4096)


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserResponse


class AuthMeResponse(BaseModel):
    id: UUID
    email: str | None
    nickname: str | None
    session_id: UUID
    authenticated_at: datetime


class AuthLogoutResponse(BaseModel):
    status: str


def auth_token_response(token_pair: AuthTokenPair) -> AuthTokenResponse:
    return AuthTokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in,
        user=user_response(token_pair.user),
    )
