from enum import StrEnum


class PermissionAuditAction(StrEnum):
    GRANT = "grant"
    REVOKE = "revoke"
    UPDATE = "update"
    RESET = "reset"
