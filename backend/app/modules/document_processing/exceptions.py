class DocumentProcessingError(Exception):
    """Base document processing service error."""


class DocumentProcessingJobNotFoundError(DocumentProcessingError):
    """Raised when a processing job cannot be found."""


class DocumentExtractionResultNotFoundError(DocumentProcessingError):
    """Raised when an extraction result cannot be found."""


class MedicalEventDraftNotFoundError(DocumentProcessingError):
    """Raised when a medical event draft cannot be found."""


class MedicalEventDraftNotPendingError(DocumentProcessingError):
    """Raised when a non-pending draft is confirmed."""


class InvalidMedicalEventDraftError(DocumentProcessingError):
    """Raised when a medical event draft payload is invalid."""
