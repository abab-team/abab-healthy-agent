from enum import StrEnum


class DocumentProcessingJobType(StrEnum):
    TEXT_READ = "text_read"
    OCR = "ocr"
    AI_EXTRACT = "ai_extract"
    EVENT_DRAFT_GENERATE = "event_draft_generate"


class DocumentProcessingStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DocumentExtractionMode(StrEnum):
    BASIC = "basic"
    STANDARD = "standard"
    DETAILED = "detailed"


class DocumentExtractionResultStatus(StrEnum):
    DRAFT = "draft"
    NEEDS_REVIEW = "needs_review"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    FAILED = "failed"


class MedicalEventDraftStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
