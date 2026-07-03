from enum import StrEnum


class SymptomRecordStatus(StrEnum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class HealthRecordSource(StrEnum):
    MANUAL = "manual"
    AI_EXTRACTED = "ai_extracted"
    IMPORTED = "imported"
    SYSTEM = "system"


class HealthRecordDraftStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class HealthRecordDraftType(StrEnum):
    SYMPTOM = "symptom"
    METRIC_CANDIDATE = "metric_candidate"
    MIXED_HEALTH_RECORD = "mixed_health_record"
