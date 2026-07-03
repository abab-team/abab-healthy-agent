from enum import StrEnum


class MedicalEventType(StrEnum):
    CHECKUP = "checkup"
    OUTPATIENT_VISIT = "outpatient_visit"
    HOSPITALIZATION = "hospitalization"
    SURGERY = "surgery"
    MEDICATION = "medication"
    ALLERGY = "allergy"
    CHRONIC_CONDITION = "chronic_condition"
    LAB_TEST = "lab_test"
    DOCTOR_ADVICE = "doctor_advice"
    FOLLOW_UP = "follow_up"
    OTHER = "other"


class MedicalEventStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class MedicalEventSource(StrEnum):
    MANUAL = "manual"
    DOCUMENT_EXTRACTED = "document_extracted"
    IMPORTED = "imported"
    SYSTEM = "system"
