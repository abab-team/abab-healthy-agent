from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.alerts.enums import AlertLevel, AlertSource, AlertType


class AlertCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alert_type: AlertType
    level: AlertLevel
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1)
    suggested_action: str | None = Field(default=None, max_length=500)
    related_entity_type: str | None = Field(default=None, max_length=100)
    related_entity_id: UUID | None = None
    trigger_reason: str | None = None
    due_at: datetime | None = None
    source: AlertSource = AlertSource.SYSTEM


class AlertTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: str | None = None


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
