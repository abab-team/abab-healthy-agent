class MedicalTimelineError(Exception):
    """Base medical timeline service error."""


class MedicalEventNotFoundError(MedicalTimelineError):
    """Raised when a medical event cannot be found."""


class InvalidMedicalEventError(MedicalTimelineError):
    """Raised when medical event input is invalid."""
