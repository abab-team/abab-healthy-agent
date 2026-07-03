class HealthProfileError(Exception):
    """Base health profile service error."""


class HealthProfileNotFoundError(HealthProfileError):
    """Raised when a health profile cannot be found."""


class HealthProfileAlreadyExistsError(HealthProfileError):
    """Raised when a user already has a health profile."""
