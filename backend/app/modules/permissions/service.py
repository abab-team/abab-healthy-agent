from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.family import repository as family_repository
from app.modules.family.enums import FamilyMemberStatus
from app.modules.permissions import policy, repository
from app.modules.permissions.enums import PermissionAuditAction
from app.modules.permissions.exceptions import (
    PermissionDeniedError,
    PermissionNotConfiguredError,
)
from app.modules.permissions.models import MemberSharePermission
from app.modules.permissions.schemas import PermissionCheckResult


def check_member_permission(
    db: Session,
    *,
    current_user_id: UUID,
    family_id: UUID | None,
    target_user_id: UUID,
    permission_type: str,
    action: str = "view",
) -> PermissionCheckResult:
    if current_user_id == target_user_id:
        return PermissionCheckResult(
            allowed=True,
            permission_type=permission_type,
            action=action,
            reason="self_access",
            visibility_scope="self",
            safe_message="允许访问自己的数据。",
        )
    if family_id is None:
        return _deny(permission_type, action, "missing_family_context")

    current_member = family_repository.get_family_member(
        db,
        family_id,
        current_user_id,
    )
    if current_member is None or current_member.status != FamilyMemberStatus.ACTIVE:
        return _deny(permission_type, action, "current_user_not_in_family")

    target_member = family_repository.get_family_member(db, family_id, target_user_id)
    if target_member is None or target_member.status != FamilyMemberStatus.ACTIVE:
        return _deny(permission_type, action, "target_user_not_in_family")

    permission = repository.get_member_share_permission(db, family_id, target_user_id)
    if permission is None:
        return _deny(permission_type, action, "permission_not_configured")

    field_name = policy.permission_field_for(permission_type, action)
    if field_name is None:
        return _deny(permission_type, action, "permission_denied")

    if (
        action == "view"
        and permission.share_all
        and permission_type in policy.SHARE_ALL_VIEW_TYPES
    ):
        return PermissionCheckResult(
            allowed=True,
            permission_type=permission_type,
            action=action,
            reason="family_share_all",
            visibility_scope="family_member_shared",
            safe_message="允许访问该成员共享的数据。",
        )

    if bool(getattr(permission, field_name)):
        return PermissionCheckResult(
            allowed=True,
            permission_type=permission_type,
            action=action,
            reason="specific_permission_allowed",
            visibility_scope="family_member_shared",
            safe_message="允许访问该成员共享的数据。",
        )

    return _deny(permission_type, action, policy.denied_reason_for(permission_type, action))


def require_member_permission(
    db: Session,
    *,
    current_user_id: UUID,
    family_id: UUID | None,
    target_user_id: UUID,
    permission_type: str,
    action: str = "view",
) -> PermissionCheckResult:
    result = check_member_permission(
        db,
        current_user_id=current_user_id,
        family_id=family_id,
        target_user_id=target_user_id,
        permission_type=permission_type,
        action=action,
    )
    if not result.allowed:
        raise PermissionDeniedError(result.safe_message)
    return result


def get_member_share_permission(
    db: Session,
    *,
    family_id: UUID,
    target_user_id: UUID,
) -> MemberSharePermission | None:
    return repository.get_member_share_permission(db, family_id, target_user_id)


def update_share_permission(
    db: Session,
    *,
    actor_user_id: UUID,
    family_id: UUID,
    target_user_id: UUID,
    updates: dict[str, bool],
    reason: str | None = None,
) -> MemberSharePermission:
    before = repository.get_member_share_permission(db, family_id, target_user_id)
    if before is None:
        raise PermissionNotConfiguredError("member share permission is not configured")
    before_snapshot = _permission_snapshot(before)
    permission = repository.update_member_share_permission(
        db,
        family_id,
        target_user_id,
        **updates,
    )
    if permission is None:
        raise PermissionNotConfiguredError("member share permission is not configured")
    repository.create_permission_audit_log(
        db,
        family_id=family_id,
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        action=PermissionAuditAction.UPDATE,
        permission_type="member_share_permissions",
        before_snapshot=before_snapshot,
        after_snapshot=_permission_snapshot(permission),
        reason=reason,
    )
    return permission


def create_default_permissions_for_member(
    db: Session,
    *,
    family_id: UUID,
    user_id: UUID,
    share_all: bool = True,
) -> MemberSharePermission:
    existing = repository.get_member_share_permission(db, family_id, user_id)
    if existing is not None:
        return existing
    return repository.create_default_share_permission(
        db,
        family_id,
        user_id,
        share_all=share_all,
    )


def _deny(
    permission_type: str,
    action: str,
    reason: str,
) -> PermissionCheckResult:
    return PermissionCheckResult(
        allowed=False,
        permission_type=permission_type,
        action=action,
        reason=reason,
        visibility_scope="none",
        safe_message=policy.SAFE_DENIED_MESSAGE,
    )


def _permission_snapshot(permission: MemberSharePermission) -> dict[str, bool]:
    return {
        field: bool(getattr(permission, field))
        for field in repository.PERMISSION_FIELDS
    }
