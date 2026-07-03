class PermissionError(Exception):
    """Base permission service error."""


class PermissionDeniedError(PermissionError):
    """Raised when permission check fails."""


class PermissionNotConfiguredError(PermissionError):
    """Raised when target member share permissions are missing."""
