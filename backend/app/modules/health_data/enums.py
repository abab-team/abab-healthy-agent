from enum import StrEnum


class MetricType(StrEnum):
    SLEEP_DURATION = "sleep_duration"
    STEPS = "steps"
    WEIGHT = "weight"
    BMI = "bmi"
    BODY_FAT = "body_fat"
    HEART_RATE = "heart_rate"
    BLOOD_OXYGEN = "blood_oxygen"
    TEMPERATURE = "temperature"
    BLOOD_GLUCOSE = "blood_glucose"
    EXERCISE_DURATION = "exercise_duration"


class MetricSource(StrEnum):
    MANUAL = "manual"
    AI_EXTRACTED = "ai_extracted"
    IMPORTED = "imported"
    DEVICE = "device"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class BloodPressureMeasurementContext(StrEnum):
    MORNING = "morning"
    EVENING = "evening"
    BEFORE_MEDICATION = "before_medication"
    AFTER_MEDICATION = "after_medication"
    AFTER_EXERCISE = "after_exercise"
    UNKNOWN = "unknown"


class BloodPressureArm(StrEnum):
    LEFT = "left"
    RIGHT = "right"
    UNKNOWN = "unknown"


class BloodPressurePosture(StrEnum):
    SITTING = "sitting"
    STANDING = "standing"
    LYING = "lying"
    UNKNOWN = "unknown"


class HealthDataImportType(StrEnum):
    MANUAL_BATCH = "manual_batch"
    CSV = "csv"
    EXCEL = "excel"
    DEVICE = "device"
    SYSTEM = "system"


class HealthDataImportStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"
    CANCELLED = "cancelled"
