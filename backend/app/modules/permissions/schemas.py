from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionCheckResult:
    allowed: bool
    permission_type: str
    action: str
    reason: str
    visibility_scope: str
    safe_message: str
