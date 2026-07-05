from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.api.validators import Reason, RequiredShortText, STRICT_MODEL_CONFIG
from app.modules.permissions.models import MemberSharePermission
from app.modules.permissions.schemas import PermissionCheckResult


class PermissionResponse(BaseModel):
    id: UUID
    family_id: UUID
    user_id: UUID
    share_all: bool
    can_view_profile: bool
    can_view_metrics: bool
    can_view_reports: bool
    can_view_symptoms: bool
    can_view_medical_events: bool
    can_view_documents: bool
    can_view_alerts: bool
    can_create_alerts: bool
    can_view_memory_summary: bool
    can_create_symptom_records: bool
    can_create_metric_records: bool
    can_upload_documents: bool
    can_create_medical_events: bool
    can_generate_reports: bool
    can_generate_doctor_visit_summary: bool
    can_export_summary: bool
    created_at: datetime
    updated_at: datetime


class PermissionUpdateRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    share_all: bool | None = None
    can_view_profile: bool | None = None
    can_view_metrics: bool | None = None
    can_view_reports: bool | None = None
    can_view_symptoms: bool | None = None
    can_view_medical_events: bool | None = None
    can_view_documents: bool | None = None
    can_view_alerts: bool | None = None
    can_create_alerts: bool | None = None
    can_view_memory_summary: bool | None = None
    can_create_symptom_records: bool | None = None
    can_create_metric_records: bool | None = None
    can_upload_documents: bool | None = None
    can_create_medical_events: bool | None = None
    can_generate_reports: bool | None = None
    can_generate_doctor_visit_summary: bool | None = None
    can_export_summary: bool | None = None
    reason: Reason = None


class PermissionCheckRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    target_user_id: UUID
    permission_type: RequiredShortText
    action: RequiredShortText = "view"


class PermissionCheckResponse(BaseModel):
    allowed: bool
    permission_type: str
    action: str
    reason: str
    visibility_scope: str
    safe_message: str


def permission_response(permission: MemberSharePermission) -> PermissionResponse:
    return PermissionResponse(
        id=permission.id,
        family_id=permission.family_id,
        user_id=permission.user_id,
        share_all=permission.share_all,
        can_view_profile=permission.can_view_profile,
        can_view_metrics=permission.can_view_metrics,
        can_view_reports=permission.can_view_reports,
        can_view_symptoms=permission.can_view_symptoms,
        can_view_medical_events=permission.can_view_medical_events,
        can_view_documents=permission.can_view_documents,
        can_view_alerts=permission.can_view_alerts,
        can_create_alerts=permission.can_create_alerts,
        can_view_memory_summary=permission.can_view_memory_summary,
        can_create_symptom_records=permission.can_create_symptom_records,
        can_create_metric_records=permission.can_create_metric_records,
        can_upload_documents=permission.can_upload_documents,
        can_create_medical_events=permission.can_create_medical_events,
        can_generate_reports=permission.can_generate_reports,
        can_generate_doctor_visit_summary=permission.can_generate_doctor_visit_summary,
        can_export_summary=permission.can_export_summary,
        created_at=permission.created_at,
        updated_at=permission.updated_at,
    )


def permission_check_response(result: PermissionCheckResult) -> PermissionCheckResponse:
    return PermissionCheckResponse(
        allowed=result.allowed,
        permission_type=result.permission_type,
        action=result.action,
        reason=result.reason,
        visibility_scope=result.visibility_scope,
        safe_message=result.safe_message,
    )
