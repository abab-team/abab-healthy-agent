from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.health_data.enums import ConfidenceLevel
from app.modules.health_record.enums import HealthRecordDraftType, HealthRecordSource


class SymptomCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_text: str = Field(min_length=1)
    symptom_name: str | None = Field(default=None, max_length=100)
    body_part: str | None = Field(default=None, max_length=100)
    severity: int | None = Field(default=None, ge=1, le=10)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    possible_trigger: str | None = Field(default=None, max_length=255)
    follow_up_needed: bool = False
    follow_up_at: datetime | None = None
    ai_summary: str | None = Field(default=None, max_length=1000)
    source: HealthRecordSource = HealthRecordSource.MANUAL


class SymptomRecordResponse(BaseModel):
    id: UUID
    user_id: UUID
    family_id: UUID | None = None
    created_by_user_id: UUID
    raw_text: str
    symptom_name: str | None = None
    body_part: str | None = None
    severity: int | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    possible_trigger: str | None = None
    follow_up_needed: bool
    follow_up_at: datetime | None = None
    status: str
    confidence_level: str
    ai_summary: str | None = None
    source: str
    created_at: datetime
    updated_at: datetime


class HealthRecordDraftCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_text: str = Field(min_length=1)
    target_display_name: str | None = Field(default=None, max_length=100)
    draft_type: HealthRecordDraftType = HealthRecordDraftType.SYMPTOM
    extracted_json: dict | None = None
    missing_fields: list[str] | None = None
    safety_flags: list[str] | None = None
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM


class HealthRecordDraftResponse(BaseModel):
    id: UUID
    user_id: UUID
    family_id: UUID | None = None
    created_by_user_id: UUID
    target_display_name: str | None = None
    raw_text: str
    draft_type: str
    extracted_json: dict
    missing_fields: list[str] | None = None
    safety_flags: list[str] | None = None
    confidence_level: str
    status: str
    confirmed_record_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
