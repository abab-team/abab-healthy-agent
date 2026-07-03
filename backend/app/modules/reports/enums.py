from enum import StrEnum


class DailyReportStatusLevel(StrEnum):
    NORMAL = "normal"
    ATTENTION = "attention"
    FOLLOW_UP = "follow_up"
    INSUFFICIENT_DATA = "insufficient_data"


class DailyReportGeneratedBy(StrEnum):
    SYSTEM = "system"
    USER = "user"
    AGENT = "agent"


class DailyReportGenerationStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
