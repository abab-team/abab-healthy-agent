class AlertsError(Exception):
    """Base alerts service error."""


class AlertNotFoundError(AlertsError):
    """Raised when an alert cannot be found."""


class InvalidAlertTransitionError(AlertsError):
    """Raised when an alert status transition is not allowed."""


class InvalidAlertError(AlertsError):
    """Raised when alert input is invalid."""
