# 模块领域：权限模块
# 领域说明：负责家庭成员之间的数据共享范围、访问策略和越权拦截。
# 文件职责：业务服务文件。编排领域规则、权限校验、仓储调用和状态流转，是模块的主要业务入口。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

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


# 函数职责：校验流程，集中执行前置条件检查，失败时抛出领域异常。
# 业务边界：校验函数不应偷偷修改业务状态，便于调用方预测副作用。
def check_member_permission(
    db: Session,
    *,
    current_user_id: UUID,
    family_id: UUID | None,
    target_user_id: UUID,
    permission_type: str,
    action: str = "view",
) -> PermissionCheckResult:
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    if current_user_id == target_user_id:
        return PermissionCheckResult(
            allowed=True,
            permission_type=permission_type,
            action=action,
            reason="self_access",
            visibility_scope="self",
            safe_message="允许访问自己的数据。",
        )
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if family_id is None:
        return _deny(permission_type, action, "missing_family_context")

    current_member = family_repository.get_family_member(
        db,
        family_id,
        current_user_id,
    )
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if current_member is None or current_member.status != FamilyMemberStatus.ACTIVE:
        return _deny(permission_type, action, "current_user_not_in_family")

    target_member = family_repository.get_family_member(db, family_id, target_user_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if target_member is None or target_member.status != FamilyMemberStatus.ACTIVE:
        return _deny(permission_type, action, "target_user_not_in_family")

    permission = repository.get_member_share_permission(db, family_id, target_user_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if permission is None:
        return _deny(permission_type, action, "permission_not_configured")

    field_name = policy.permission_field_for(permission_type, action)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if field_name is None:
        return _deny(permission_type, action, "permission_denied")

    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
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

    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
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


# 函数职责：业务函数，封装 权限模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def require_member_permission(
    db: Session,
    *,
    current_user_id: UUID,
    family_id: UUID | None,
    target_user_id: UUID,
    permission_type: str,
    action: str = "view",
) -> PermissionCheckResult:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    result = check_member_permission(
        db,
        current_user_id=current_user_id,
        family_id=family_id,
        target_user_id=target_user_id,
        permission_type=permission_type,
        action=action,
    )
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if not result.allowed:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise PermissionDeniedError(result.safe_message)
    return result


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_member_share_permission(
    db: Session,
    *,
    family_id: UUID,
    target_user_id: UUID,
) -> MemberSharePermission | None:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    return repository.get_member_share_permission(db, family_id, target_user_id)


# 函数职责：更新流程，在校验当前状态后修改已有对象或推进状态机。
# 业务边界：更新动作要保持幂等性和状态合法性，避免跳过必要确认。
def update_share_permission(
    db: Session,
    *,
    actor_user_id: UUID,
    family_id: UUID,
    target_user_id: UUID,
    updates: dict[str, bool],
    reason: str | None = None,
) -> MemberSharePermission:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    before = repository.get_member_share_permission(db, family_id, target_user_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if before is None:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise PermissionNotConfiguredError("member share permission is not configured")
    before_snapshot = _permission_snapshot(before)
    permission = repository.update_member_share_permission(
        db,
        family_id,
        target_user_id,
        **updates,
    )
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if permission is None:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
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


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def create_default_permissions_for_member(
    db: Session,
    *,
    family_id: UUID,
    user_id: UUID,
    share_all: bool = True,
) -> MemberSharePermission:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    existing = repository.get_member_share_permission(db, family_id, user_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if existing is not None:
        return existing
    return repository.create_default_share_permission(
        db,
        family_id,
        user_id,
        share_all=share_all,
    )


# 函数职责：业务函数，封装 权限模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def _deny(
    permission_type: str,
    action: str,
    reason: str,
) -> PermissionCheckResult:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    return PermissionCheckResult(
        allowed=False,
        permission_type=permission_type,
        action=action,
        reason=reason,
        visibility_scope="none",
        safe_message=policy.SAFE_DENIED_MESSAGE,
    )


# 函数职责：业务函数，封装 权限模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def _permission_snapshot(permission: MemberSharePermission) -> dict[str, bool]:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    return {
        field: bool(getattr(permission, field))
        for field in repository.PERMISSION_FIELDS
    }
