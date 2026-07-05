# 模块领域：权限模块
# 领域说明：负责家庭成员之间的数据共享范围、访问策略和越权拦截。
# 文件职责：仓储文件。封装数据库查询和写入细节，让业务服务只表达业务意图。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.permissions.enums import PermissionAuditAction
from app.modules.permissions.models import MemberSharePermission, PermissionAuditLog


PERMISSION_FIELDS = {
    "share_all",
    "can_view_profile",
    "can_view_metrics",
    "can_view_reports",
    "can_view_symptoms",
    "can_view_medical_events",
    "can_view_documents",
    "can_view_alerts",
    "can_create_alerts",
    "can_view_memory_summary",
    "can_create_symptom_records",
    "can_create_metric_records",
    "can_upload_documents",
    "can_create_medical_events",
    "can_generate_reports",
    "can_generate_doctor_visit_summary",
    "can_export_summary",
}


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_member_share_permission(
    db: Session,
    family_id: UUID,
    user_id: UUID,
) -> MemberSharePermission | None:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    return db.scalar(
        select(MemberSharePermission).where(
            MemberSharePermission.family_id == family_id,
            MemberSharePermission.user_id == user_id,
        ),
    )


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def create_default_share_permission(
    db: Session,
    family_id: UUID,
    user_id: UUID,
    *,
    share_all: bool = True,
) -> MemberSharePermission:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    permission = MemberSharePermission(
        family_id=family_id,
        user_id=user_id,
        share_all=share_all,
        can_view_profile=share_all,
        can_view_metrics=share_all,
        can_view_reports=share_all,
        can_view_symptoms=share_all,
        can_view_medical_events=share_all,
        can_view_documents=share_all,
        can_view_alerts=share_all,
        can_create_alerts=share_all,
        can_view_memory_summary=share_all,
        can_create_symptom_records=share_all,
        can_create_metric_records=share_all,
        can_upload_documents=share_all,
        can_create_medical_events=share_all,
        can_generate_reports=share_all,
        can_generate_doctor_visit_summary=share_all,
        can_export_summary=share_all,
    )
    db.add(permission)
    db.flush()
    return permission


# 函数职责：更新流程，在校验当前状态后修改已有对象或推进状态机。
# 业务边界：更新动作要保持幂等性和状态合法性，避免跳过必要确认。
def update_member_share_permission(
    db: Session,
    family_id: UUID,
    user_id: UUID,
    **fields: bool,
) -> MemberSharePermission | None:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    permission = get_member_share_permission(db, family_id, user_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if permission is None:
        return None
    # 循环说明：逐项处理集合中的业务对象，保持每个元素处理逻辑一致。
    for field, value in fields.items():
        # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
        if field in PERMISSION_FIELDS:
            setattr(permission, field, value)
    db.flush()
    return permission


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def create_permission_audit_log(
    db: Session,
    *,
    family_id: UUID,
    actor_user_id: UUID,
    target_user_id: UUID,
    action: PermissionAuditAction,
    permission_type: str | None = None,
    before_snapshot: dict | None = None,
    after_snapshot: dict | None = None,
    reason: str | None = None,
) -> PermissionAuditLog:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    log = PermissionAuditLog(
        family_id=family_id,
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        action=action,
        permission_type=permission_type,
        before_snapshot=before_snapshot,
        after_snapshot=after_snapshot,
        reason=reason,
    )
    db.add(log)
    db.flush()
    return log


# 函数职责：列表查询流程，按过滤条件返回一组对象，并保持排序、分页或范围语义稳定。
# 业务边界：返回集合时要避免把未授权数据暴露给调用方。
def list_permissions_for_family(
    db: Session,
    family_id: UUID,
) -> list[MemberSharePermission]:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    return list(
        db.scalars(
            select(MemberSharePermission).where(
                MemberSharePermission.family_id == family_id,
            ),
        ),
    )
