from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.api.validators import Note, RequiredAlertText, ShortText, STRICT_MODEL_CONFIG, SuggestedAction, Title, TriggerReason
from app.modules.alerts.enums import AlertLevel, AlertSource, AlertType


class AlertCreateRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    alert_type: AlertType
    level: AlertLevel
    title: Title
    message: RequiredAlertText
    suggested_action: SuggestedAction = None
    related_entity_type: ShortText = None
    related_entity_id: UUID | None = None
    trigger_reason: TriggerReason = None
    due_at: datetime | None = None
    source: AlertSource = AlertSource.SYSTEM


class AlertTransitionRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    note: Note = None


class AlertResponse(BaseModel):
    id: UUID
    user_id: UUID
    family_id: UUID | None = None
    created_by_user_id: UUID | None = None
    alert_type: str
    level: str
    title: str
    message: str
    suggested_action: str | None = None
    related_entity_type: str | None = None
    related_entity_id: UUID | None = None
    trigger_reason: str | None = None
    status: str
    due_at: datetime | None = None
    resolved_at: datetime | None = None
    source: str
    created_at: datetime
    updated_at: datetime
