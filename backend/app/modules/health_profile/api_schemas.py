from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.validators import Description, STRICT_MODEL_CONFIG
from app.modules.health_profile.enums import BloodType
from app.modules.identity.enums import Gender


class HealthProfileUpdateRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    height_cm: float | None = Field(default=None, ge=30, le=260)
    gender: Gender | None = None
    birth_date: date | None = None
    blood_type: BloodType | None = None
    health_goal: Description = None
    chronic_conditions_summary: Description = None
    allergy_summary: Description = None
    medication_summary: Description = None


class HealthProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    height_cm: float | None = None
    gender: str | None = None
    birth_date: date | None = None
    blood_type: str | None = None
    health_goal: str | None = None
    chronic_conditions_summary: str | None = None
    allergy_summary: str | None = None
    medication_summary: str | None = None
    created_at: datetime
    updated_at: datetime
