from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.api.validators import DoctorAdvice, HospitalOrOrg, Department, JsonList, ShortText, STRICT_MODEL_CONFIG, SummaryText, Title
from app.modules.health_data.enums import ConfidenceLevel
from app.modules.medical_timeline.enums import MedicalEventSource, MedicalEventType


class MedicalEventCreateRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    event_type: MedicalEventType
    title: Title
    event_date: date | None = None
    event_date_text: ShortText = None
    hospital_or_org: HospitalOrOrg = None
    department: Department = None
    diagnosis_text: SummaryText = None
    summary: SummaryText = None
    doctor_advice: DoctorAdvice = None
    medications: JsonList = None
    key_findings: JsonList = None
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
