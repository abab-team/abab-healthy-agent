from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.identity.enums import Gender, UserStatus
from app.modules.identity.schemas import UserPublic


class UserCreateRequest(BaseModel):
    email: str | None = None
    phone: str | None = None
    nickname: str | None = None
    gender: Gender | None = None
    birth_date: date | None = None


class UserProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nickname: str | None = None
    avatar_url: str | None = None
    gender: Gender | None = None
    birth_date: date | None = None


class UserResponse(BaseModel):
    id: UUID
    email: str | None
    phone: str | None
    nickname: str | None
    avatar_url: str | None
    gender: Gender | None
    birth_date: date | None
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None


def user_response(user: UserPublic) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        phone=user.phone,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        gender=user.gender,
        birth_date=user.birth_date,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )
