from enum import StrEnum


class DocumentType(StrEnum):
    CHECKUP_REPORT = "checkup_report"
    MEDICAL_RECORD = "medical_record"
    LAB_TEST = "lab_test"
    SURGERY_RECORD = "surgery_record"
    DISCHARGE_SUMMARY = "discharge_summary"
    PRESCRIPTION = "prescription"
    DOCTOR_ADVICE = "doctor_advice"
    IMAGE_NOTE = "image_note"
    OTHER = "other"


class DocumentExtractStatus(StrEnum):
    NOT_STARTED = "not_started"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"
    CONFIRMED = "confirmed"


class DocumentVisibility(StrEnum):
    PRIVATE = "private"
    FAMILY_SHARED = "family_shared"


class DocumentSource(StrEnum):
    UPLOAD = "upload"
    MANUAL = "manual"
    IMPORTED = "imported"
    SYSTEM = "system"
