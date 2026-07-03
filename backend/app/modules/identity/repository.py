from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.identity.enums import Gender, UserStatus
from app.modules.identity.models import User


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_user_by_phone(db: Session, phone: str) -> User | None:
    return db.scalar(select(User).where(User.phone == phone))


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
) -> User:
    user = User(
        email=email,
        phone=phone,
        nickname=nickname,
        password_hash=password_hash,
        gender=gender,
        birth_date=birth_date,
        status=status,
    )
    db.add(user)
    db.flush()
    return user


def update_last_login_at(
    db: Session,
    user_id: UUID,
    login_at: datetime,
) -> User | None:
    user = get_user_by_id(db, user_id)
    if user is None:
        return None
    user.last_login_at = login_at
    db.flush()
    return user


def list_users_by_ids(db: Session, user_ids: list[UUID]) -> list[User]:
    if not user_ids:
        return []
    return list(db.scalars(select(User).where(User.id.in_(user_ids))))
