from enum import StrEnum


class AuditAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    EXPORT = "export"
    SHARE = "share"
    LOGIN = "login"
    LOGOUT = "logout"
    PERMISSION_CHANGE = "permission_change"
    AGENT_RUN = "agent_run"
    TOOL_CALL = "tool_call"
    SAFETY_BLOCK = "safety_block"


class AuditResourceType(StrEnum):
    USER = "user"
    FAMILY = "family"
    FAMILY_MEMBER = "family_member"
    PERMISSION = "permission"
    HEALTH_PROFILE = "health_profile"
    HEALTH_METRIC = "health_metric"
    BLOOD_PRESSURE_RECORD = "blood_pressure_record"
    SYMPTOM_RECORD = "symptom_record"
    MEDICAL_EVENT = "medical_event"
    MEDICAL_DOCUMENT = "medical_document"
    DAILY_REPORT = "daily_report"
    ALERT = "alert"
    AGENT_TRACE = "agent_trace"
    EXPORT_FILE = "export_file"
    SYSTEM = "system"


class DataAccessCategory(StrEnum):
    PROFILE = "profile"
    METRICS = "metrics"
    REPORTS = "reports"
    SYMPTOMS = "symptoms"
    MEDICAL_EVENTS = "medical_events"
    DOCUMENTS = "documents"
    ALERTS = "alerts"
    MEMORY_SUMMARY = "memory_summary"
    AUDIT = "audit"


class DataAccessAction(StrEnum):
    VIEW = "view"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    GENERATE = "generate"
    EXPORT = "export"


class PrivacyEventType(StrEnum):
    PERMISSION_UPDATED = "permission_updated"
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_DELETED = "document_deleted"
    DATA_EXPORTED = "data_exported"
    SHARE_LINK_CREATED = "share_link_created"
    SHARE_LINK_REVOKED = "share_link_revoked"
    AGENT_ACCESSED_DATA = "agent_accessed_data"
    USER_DELETED_DATA = "user_deleted_data"
    ACCOUNT_DELETED = "account_deleted"
