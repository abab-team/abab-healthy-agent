from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from app.modules.identity.enums import Gender, UserStatus
from app.modules.identity.models import User


@dataclass(frozen=True)
class UserPublic:
    id: UUID
    phone: str | None
    email: str | None
    nickname: str | None
    avatar_url: str | None
    gender: Gender | None
    birth_date: date | None
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None


def to_user_public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        phone=user.phone,
        email=user.email,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        gender=user.gender,
        birth_date=user.birth_date,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )
