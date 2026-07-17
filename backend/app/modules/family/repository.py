# 模块领域：家庭成员模块
# 领域说明：负责家庭、成员关系、邀请流程和自然语言成员称呼解析。
# 文件职责：仓储文件。封装数据库查询和写入细节，让业务服务只表达业务意图。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.family.enums import (
    FamilyInvitationStatus,
    FamilyMemberStatus,
    FamilyRole,
)
from app.modules.family.models import Family, FamilyInvitation, FamilyMember


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def create_family(db: Session, *, name: str, owner_user_id: UUID) -> Family:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    family = Family(name=name, owner_user_id=owner_user_id)
    db.add(family)
    db.flush()
    return family


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_family_by_id(db: Session, family_id: UUID) -> Family | None:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    return db.get(Family, family_id)


# 函数职责：列表查询流程，按过滤条件返回一组对象，并保持排序、分页或范围语义稳定。
# 业务边界：返回集合时要避免把未授权数据暴露给调用方。
def list_families_for_user(db: Session, user_id: UUID) -> list[Family]:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    return list(
        db.scalars(
            select(Family)
            .join(FamilyMember, FamilyMember.family_id == Family.id)
            .where(
                FamilyMember.user_id == user_id,
                FamilyMember.status == FamilyMemberStatus.ACTIVE,
            ),
        ),
    )


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def create_family_member(
    db: Session,
    *,
    family_id: UUID,
    user_id: UUID,
    role: FamilyRole = FamilyRole.MEMBER,
    relationship_label: str | None = None,
    display_name: str | None = None,
    status: FamilyMemberStatus = FamilyMemberStatus.ACTIVE,
) -> FamilyMember:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    member = FamilyMember(
        family_id=family_id,
        user_id=user_id,
        role=role,
        relationship_label=relationship_label,
        display_name=display_name,
        status=status,
    )
    db.add(member)
    db.flush()
    return member


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_family_member(
    db: Session,
    family_id: UUID,
    user_id: UUID,
) -> FamilyMember | None:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    return db.scalar(
        select(FamilyMember).where(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == user_id,
        ),
    )


# 函数职责：列表查询流程，按过滤条件返回一组对象，并保持排序、分页或范围语义稳定。
# 业务边界：返回集合时要避免把未授权数据暴露给调用方。
def list_family_members(db: Session, family_id: UUID) -> list[FamilyMember]:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    return list(
        db.scalars(
            select(FamilyMember).where(FamilyMember.family_id == family_id),
        ),
    )


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def find_members_by_relationship_label(
    db: Session,
    family_id: UUID,
    relationship_label: str,
) -> list[FamilyMember]:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    return list(
        db.scalars(
            select(FamilyMember).where(
                FamilyMember.family_id == family_id,
                FamilyMember.relationship_label == relationship_label,
                FamilyMember.status == FamilyMemberStatus.ACTIVE,
            ),
        ),
    )


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def find_members_by_display_name(
    db: Session,
    family_id: UUID,
    display_name: str,
) -> list[FamilyMember]:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    return list(
        db.scalars(
            select(FamilyMember).where(
                FamilyMember.family_id == family_id,
                FamilyMember.display_name == display_name,
                FamilyMember.status == FamilyMemberStatus.ACTIVE,
            ),
        ),
    )


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def create_family_invitation(
    db: Session,
    *,
    family_id: UUID,
    inviter_user_id: UUID,
    invite_code: str,
    expires_at: datetime,
    invitee_phone: str | None = None,
    invitee_email: str | None = None,
    status: FamilyInvitationStatus = FamilyInvitationStatus.PENDING,
) -> FamilyInvitation:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    invitation = FamilyInvitation(
        family_id=family_id,
        inviter_user_id=inviter_user_id,
        invite_code=invite_code,
        invitee_phone=invitee_phone,
        invitee_email=invitee_email,
        status=status,
        expires_at=expires_at,
    )
    db.add(invitation)
    db.flush()
    return invitation


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_invitation_by_code(
    db: Session,
    invite_code: str,
) -> FamilyInvitation | None:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    return db.scalar(
        select(FamilyInvitation).where(FamilyInvitation.invite_code == invite_code),
    )


def accept_family_invitation(db: Session, invitation: FamilyInvitation, *, user_id: UUID, accepted_at: datetime) -> FamilyInvitation:
    invitation.status = FamilyInvitationStatus.ACCEPTED
    invitation.accepted_by_user_id = user_id
    invitation.accepted_at = accepted_at
    db.flush()
    return invitation
