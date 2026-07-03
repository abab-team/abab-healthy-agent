from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.modules.health_profile.enums import BloodType
from app.modules.health_profile.models import HealthProfile
from app.modules.identity.enums import Gender


@dataclass(frozen=True)
class HealthProfileSnapshot:
    user_id: UUID
    height_cm: float | None
    gender: Gender | None
    birth_date: date | None
    blood_type: BloodType | None
    health_goal: str | None
    chronic_conditions_summary: str | None
    allergy_summary: str | None
    medication_summary: str | None


def to_profile_snapshot(profile: HealthProfile) -> HealthProfileSnapshot:
    return HealthProfileSnapshot(
        user_id=profile.user_id,
        height_cm=float(profile.height_cm) if profile.height_cm is not None else None,
        gender=profile.gender,
        birth_date=profile.birth_date,
        blood_type=profile.blood_type,
        health_goal=profile.health_goal,
        chronic_conditions_summary=profile.chronic_conditions_summary,
        allergy_summary=profile.allergy_summary,
        medication_summary=profile.medication_summary,
    )
