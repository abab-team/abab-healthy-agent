from enum import StrEnum


class AlertType(StrEnum):
    METRIC_ATTENTION = "metric_attention"
    SYMPTOM_FOLLOW_UP = "symptom_follow_up"
    MEDICAL_FOLLOW_UP = "medical_follow_up"
    MEDICATION_REMINDER = "medication_reminder"
    DATA_MISSING = "data_missing"
    DOCUMENT_REVIEW = "document_review"


class AlertLevel(StrEnum):
    INFO = "info"
    ATTENTION = "attention"
    IMPORTANT = "important"
    URGENT = "urgent"


class AlertStatus(StrEnum):
    ACTIVE = "active"
    READ = "read"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class AlertSource(StrEnum):
    RULE = "rule"
    AGENT = "agent"
    USER = "user"
    SYSTEM = "system"


class AlertEventType(StrEnum):
    CREATED = "created"
    READ = "read"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    REOPENED = "reopened"
    EXPIRED = "expired"
