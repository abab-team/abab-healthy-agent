from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.health_profile.enums import BloodType
from app.modules.identity.enums import Gender


class HealthProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    height_cm: float | None = Field(default=None, ge=30, le=260)
    gender: Gender | None = None
    birth_date: date | None = None
    blood_type: BloodType | None = None
    health_goal: str | None = Field(default=None, max_length=500)
    chronic_conditions_summary: str | None = Field(default=None, max_length=1000)
    allergy_summary: str | None = Field(default=None, max_length=1000)
    medication_summary: str | None = Field(default=None, max_length=1000)


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
