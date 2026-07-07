from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.identity.schemas import UserPublic


@dataclass(frozen=True)
class AuthTokenPair:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserPublic
    access_expires_at: datetime


@dataclass(frozen=True)
class AuthenticatedUser:
    user: UserPublic
    session_id: UUID
