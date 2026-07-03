class HealthRecordError(Exception):
    """Base health record service error."""


class SymptomRecordNotFoundError(HealthRecordError):
    """Raised when a symptom record cannot be found."""


class HealthRecordDraftNotFoundError(HealthRecordError):
    """Raised when a health record draft cannot be found."""


class HealthRecordDraftNotPendingError(HealthRecordError):
    """Raised when a non-pending draft is confirmed."""


class HealthRecordDraftTypeUnsupportedError(HealthRecordError):
    """Raised when a draft type cannot create a symptom record."""


class InvalidHealthRecordDraftError(HealthRecordError):
    """Raised when draft payload is invalid."""
