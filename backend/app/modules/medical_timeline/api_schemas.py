from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.health_data.enums import ConfidenceLevel
from app.modules.medical_timeline.enums import MedicalEventSource, MedicalEventType


class MedicalEventCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: MedicalEventType
    title: str = Field(min_length=1, max_length=200)
    event_date: date | None = None
    event_date_text: str | None = Field(default=None, max_length=100)
    hospital_or_org: str | None = Field(default=None, max_length=200)
    department: str | None = Field(default=None, max_length=100)
    diagnosis_text: str | None = Field(default=None, max_length=500)
    summary: str | None = None
    doctor_advice: str | None = None
    medications: list[dict] | None = None
    key_findings: list[dict] | None = None
    follow_up_needed: bool = False
    follow_up_at: datetime | None = None
    related_document_id: UUID | None = None
    source: MedicalEventSource = MedicalEventSource.MANUAL
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    timeline_visible: bool = True


class MedicalEventResponse(BaseModel):
    id: UUID
    user_id: UUID
    family_id: UUID | None = None
    created_by_user_id: UUID
    event_type: str
    title: str
    event_date: date | None = None
    event_date_text: str | None = None
    hospital_or_org: str | None = None
    department: str | None = None
    diagnosis_text: str | None = None
    summary: str | None = None
    doctor_advice: str | None = None
    medications: list[dict] | None = None
    key_findings: list[dict] | None = None
    follow_up_needed: bool
    follow_up_at: datetime | None = None
    related_document_id: UUID | None = None
    source: str
    confidence_level: str
    timeline_visible: bool
    status: str
    created_at: datetime
    updated_at: datetime
