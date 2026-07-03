from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.health_profile.enums import BloodType
from app.modules.health_profile.models import HealthProfile
from app.modules.identity.enums import Gender


def get_profile_by_user_id(db: Session, user_id: UUID) -> HealthProfile | None:
    return db.scalar(select(HealthProfile).where(HealthProfile.user_id == user_id))


def create_profile(
    db: Session,
    *,
    user_id: UUID,
    height_cm: float | None = None,
    gender: Gender | None = None,
    birth_date: date | None = None,
    blood_type: BloodType | None = None,
    health_goal: str | None = None,
    chronic_conditions_summary: str | None = None,
    allergy_summary: str | None = None,
    medication_summary: str | None = None,
) -> HealthProfile:
    profile = HealthProfile(
        user_id=user_id,
        height_cm=height_cm,
        gender=gender,
        birth_date=birth_date,
        blood_type=blood_type,
        health_goal=health_goal,
        chronic_conditions_summary=chronic_conditions_summary,
        allergy_summary=allergy_summary,
        medication_summary=medication_summary,
    )
    db.add(profile)
    db.flush()
    return profile


def update_profile(db: Session, user_id: UUID, **fields: object) -> HealthProfile | None:
    profile = get_profile_by_user_id(db, user_id)
    if profile is None:
        return None
    allowed = {
        "height_cm",
        "gender",
        "birth_date",
        "blood_type",
        "health_goal",
        "chronic_conditions_summary",
        "allergy_summary",
        "medication_summary",
    }
    for field, value in fields.items():
        if field in allowed:
            setattr(profile, field, value)
    db.flush()
    return profile


def get_or_create_profile(
    db: Session,
    user_id: UUID,
    **defaults: object,
) -> HealthProfile:
    profile = get_profile_by_user_id(db, user_id)
    if profile is not None:
        return profile
    return create_profile(db, user_id=user_id, **defaults)


def list_profiles_by_user_ids(
    db: Session,
    user_ids: list[UUID],
) -> list[HealthProfile]:
    if not user_ids:
        return []
    return list(
        db.scalars(select(HealthProfile).where(HealthProfile.user_id.in_(user_ids))),
    )
