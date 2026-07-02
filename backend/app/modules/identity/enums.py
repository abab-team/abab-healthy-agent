from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DELETED = "deleted"


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class AuthProvider(StrEnum):
    PHONE = "phone"
    EMAIL = "email"
    WECHAT = "wechat"
    GOOGLE = "google"
    APPLE = "apple"
