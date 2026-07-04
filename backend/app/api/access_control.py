from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.api.errors import raise_permission_denied
from app.modules.audit import service as audit_service
from app.modules.permissions import service as permission_service
from app.modules.permissions.schemas import PermissionCheckResult


@dataclass(frozen=True)
class AccessContext:
    allowed: bool
    current_user_id: UUID
    target_user_id: UUID
    family_id: UUID | None
    permission_type: str
    action: str
    data_category: str
    access_reason: str
    permission_result: PermissionCheckResult
    visibility_scope: str


def require_self_or_family_permission(
    db: Session,
    *,
    current_user_id: UUID,
    target_user_id: UUID,
    family_id: UUID | None = None,
    permission_type: str,
    action: str,
    data_category: str,
    access_reason: str,
    resource_type: str | None = None,
    resource_id: UUID | None = None,
) -> AccessContext:
    result = permission_service.check_member_permission(
        db,
        current_user_id=current_user_id,
        family_id=family_id,
        target_user_id=target_user_id,
        permission_type=permission_type,
        action=action,
    )
    permission_summary = _permission_summary(result)
    audit_service.log_data_access(
        db,
        actor_user_id=current_user_id,
        family_id=family_id,
        target_user_id=target_user_id,
        data_category=data_category,
        action=action,
        access_reason=access_reason or result.reason,
        allowed=result.allowed,
        permission_result=permission_summary,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    db.commit()
    if not result.allowed:
        raise_permission_denied(result.safe_message)
    return AccessContext(
        allowed=True,
        current_user_id=current_user_id,
        target_user_id=target_user_id,
        family_id=family_id,
        permission_type=permission_type,
        action=action,
        data_category=data_category,
        access_reason=access_reason or result.reason,
        permission_result=result,
        visibility_scope=result.visibility_scope,
    )


def _permission_summary(result: PermissionCheckResult) -> dict:
    return {
        "allowed": result.allowed,
        "permission_type": result.permission_type,
        "action": result.action,
        "reason": result.reason,
        "visibility_scope": result.visibility_scope,
    }
