from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.identity import repository
from app.modules.identity.enums import Gender, UserStatus
from app.modules.identity.exceptions import (
    UserAlreadyExistsError,
    UserContactRequiredError,
    UserNotFoundError,
)
from app.modules.identity.models import User
from app.modules.identity.schemas import UserPublic, to_user_public


def create_user(
    db: Session,
    *,
    email: str | None = None,
    phone: str | None = None,
    nickname: str | None = None,
    password_hash: str | None = None,
    gender: Gender | None = None,
    birth_date: date | None = None,
    status: UserStatus = UserStatus.ACTIVE,
) -> UserPublic:
    if email is None and phone is None:
        raise UserContactRequiredError("email or phone is required to create a user")
    if email is not None and repository.get_user_by_email(db, email) is not None:
        raise UserAlreadyExistsError("email already exists")
    if phone is not None and repository.get_user_by_phone(db, phone) is not None:
        raise UserAlreadyExistsError("phone already exists")

    user = repository.create_user(
        db,
        email=email,
        phone=phone,
        nickname=nickname,
        password_hash=password_hash,
        gender=gender,
        birth_date=birth_date,
        status=status,
    )
    return to_user_public(user)


def get_user(db: Session, user_id: UUID) -> UserPublic | None:
    user = repository.get_user_by_id(db, user_id)
    return to_user_public(user) if user is not None else None


def get_user_by_email(db: Session, email: str) -> UserPublic | None:
    user = repository.get_user_by_email(db, email)
    return to_user_public(user) if user is not None else None


def get_user_by_phone(db: Session, phone: str) -> UserPublic | None:
    user = repository.get_user_by_phone(db, phone)
    return to_user_public(user) if user is not None else None


def ensure_user_exists(db: Session, user_id: UUID) -> User:
    user = repository.get_user_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError("user not found")
    return user


def update_profile(
    db: Session,
    user_id: UUID,
    *,
    nickname: str | None = None,
    avatar_url: str | None = None,
    gender: Gender | None = None,
    birth_date: date | None = None,
) -> UserPublic:
    user = ensure_user_exists(db, user_id)
    if nickname is not None:
        user.nickname = nickname
    if avatar_url is not None:
        user.avatar_url = avatar_url
    if gender is not None:
        user.gender = gender
    if birth_date is not None:
        user.birth_date = birth_date
    db.flush()
    return to_user_public(user)
