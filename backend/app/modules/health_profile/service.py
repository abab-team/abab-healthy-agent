from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.health_profile import repository
from app.modules.health_profile.exceptions import HealthProfileNotFoundError
from app.modules.health_profile.models import HealthProfile
from app.modules.health_profile.schemas import HealthProfileSnapshot, to_profile_snapshot


def get_profile(db: Session, user_id: UUID) -> HealthProfile | None:
    return repository.get_profile_by_user_id(db, user_id)


def ensure_profile(db: Session, user_id: UUID) -> HealthProfile:
    return repository.get_or_create_profile(db, user_id)


def create_or_update_profile(
    db: Session,
    user_id: UUID,
    fields: dict,
) -> HealthProfile:
    profile = repository.get_profile_by_user_id(db, user_id)
    if profile is None:
        return repository.create_profile(db, user_id=user_id, **fields)
    updated = repository.update_profile(db, user_id, **fields)
    if updated is None:
        raise HealthProfileNotFoundError("health profile not found")
    return updated


def update_health_goal(
    db: Session,
    user_id: UUID,
    health_goal: str,
) -> HealthProfile:
    return create_or_update_profile(db, user_id, {"health_goal": health_goal})


def update_profile_summaries(
    db: Session,
    user_id: UUID,
    *,
    chronic_conditions_summary: str | None = None,
    allergy_summary: str | None = None,
    medication_summary: str | None = None,
) -> HealthProfile:
    fields = {
        "chronic_conditions_summary": chronic_conditions_summary,
        "allergy_summary": allergy_summary,
        "medication_summary": medication_summary,
    }
    return create_or_update_profile(
        db,
        user_id,
        {key: value for key, value in fields.items() if value is not None},
    )


def get_profile_snapshot(db: Session, user_id: UUID) -> HealthProfileSnapshot:
    profile = ensure_profile(db, user_id)
    return to_profile_snapshot(profile)
