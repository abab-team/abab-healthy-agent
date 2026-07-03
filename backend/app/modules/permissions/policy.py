from __future__ import annotations


SAFE_DENIED_MESSAGE = "你目前没有权限查看该成员的这类健康数据。可以请对方在家庭共享设置中开启相关权限。"

VIEW_PERMISSION_FIELDS = {
    "profile": "can_view_profile",
    "metrics": "can_view_metrics",
    "reports": "can_view_reports",
    "symptoms": "can_view_symptoms",
    "medical_events": "can_view_medical_events",
    "documents": "can_view_documents",
    "alerts": "can_view_alerts",
    "memory_summary": "can_view_memory_summary",
}

CREATE_PERMISSION_FIELDS = {
    "symptoms": "can_create_symptom_records",
    "metrics": "can_create_metric_records",
    "documents": "can_upload_documents",
    "medical_events": "can_create_medical_events",
}

GENERATE_PERMISSION_FIELDS = {
    "reports": "can_generate_reports",
    "doctor_visit_summary": "can_generate_doctor_visit_summary",
}

SHARE_ALL_VIEW_TYPES = {
    "profile",
    "metrics",
    "reports",
    "symptoms",
    "medical_events",
    "alerts",
    "memory_summary",
}


def permission_field_for(permission_type: str, action: str) -> str | None:
    if action == "view":
        return VIEW_PERMISSION_FIELDS.get(permission_type)
    if action in {"create", "update", "delete"}:
        return CREATE_PERMISSION_FIELDS.get(permission_type)
    if action == "generate":
        return GENERATE_PERMISSION_FIELDS.get(permission_type)
    if action == "export":
        return "can_export_summary"
    return None


def denied_reason_for(permission_type: str, action: str) -> str:
    if permission_type == "documents":
        return "documents_not_shared"
    if permission_type == "symptoms":
        return "symptoms_not_shared"
    if permission_type == "medical_events":
        return "medical_events_not_shared"
    if action in {"create", "update", "delete"}:
        return "create_not_allowed"
    if action == "export":
        return "export_not_allowed"
    return "permission_denied"
