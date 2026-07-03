class ReportsError(Exception):
    """Base reports service error."""


class DailyReportNotFoundError(ReportsError):
    """Raised when a daily report cannot be found."""


class InvalidDailyReportError(ReportsError):
    """Raised when daily report input is invalid."""
