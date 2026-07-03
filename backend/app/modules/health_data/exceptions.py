class HealthDataError(Exception):
    """Base health data service error."""


class HealthMetricNotFoundError(HealthDataError):
    """Raised when a metric cannot be found."""


class BloodPressureRecordNotFoundError(HealthDataError):
    """Raised when a blood pressure record cannot be found."""


class InvalidMetricValueError(HealthDataError):
    """Raised when a metric value is invalid."""


class InvalidBloodPressureValueError(HealthDataError):
    """Raised when a blood pressure value is invalid."""


class HealthDataImportJobNotFoundError(HealthDataError):
    """Raised when an import job cannot be found."""
