# 模块领域：家庭成员模块
# 领域说明：负责家庭、成员关系、邀请流程和自然语言成员称呼解析。
# 文件职责：业务服务文件。编排领域规则、权限校验、仓储调用和状态流转，是模块的主要业务入口。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.family import member_resolver, repository
from app.modules.family.enums import FamilyMemberStatus, FamilyRole
from app.modules.family.exceptions import (
    FamilyMemberAlreadyExistsError,
    FamilyMemberNotFoundError,
    FamilyNotFoundError,
    MemberReferenceAmbiguousError,
    MemberReferenceNotFoundError,
)
from app.modules.family.models import Family, FamilyMember
from app.modules.family.schemas import MemberCandidate, MemberResolutionResult
from app.modules.identity.service import ensure_user_exists


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def create_family_with_owner(
    db: Session,
    *,
    owner_user_id: UUID,
    family_name: str,
    owner_display_name: str = "本人",
) -> Family:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    ensure_user_exists(db, owner_user_id)
    family = repository.create_family(
        db,
        name=family_name,
        owner_user_id=owner_user_id,
    )
    repository.create_family_member(
        db,
        family_id=family.id,
        user_id=owner_user_id,
        role=FamilyRole.OWNER,
        relationship_label="本人",
        display_name=owner_display_name,
        status=FamilyMemberStatus.ACTIVE,
    )
    return family


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def add_registered_member(
    db: Session,
    *,
    family_id: UUID,
    user_id: UUID,
    relationship_label: str,
    display_name: str,
    role: FamilyRole = FamilyRole.MEMBER,
) -> FamilyMember:
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    if repository.get_family_by_id(db, family_id) is None:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise FamilyNotFoundError("family not found")
    ensure_user_exists(db, user_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if repository.get_family_member(db, family_id, user_id) is not None:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise FamilyMemberAlreadyExistsError("user already belongs to family")
    return repository.create_family_member(
        db,
        family_id=family_id,
        user_id=user_id,
        role=role,
        relationship_label=relationship_label,
        display_name=display_name,
        status=FamilyMemberStatus.ACTIVE,
    )


# 函数职责：列表查询流程，按过滤条件返回一组对象，并保持排序、分页或范围语义稳定。
# 业务边界：返回集合时要避免把未授权数据暴露给调用方。
def list_family_members(db: Session, family_id: UUID) -> list[FamilyMember]:
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    if repository.get_family_by_id(db, family_id) is None:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise FamilyNotFoundError("family not found")
    return repository.list_family_members(db, family_id)


# 函数职责：列表查询流程，按过滤条件返回一组对象，并保持排序、分页或范围语义稳定。
# 业务边界：返回集合时要避免把未授权数据暴露给调用方。
def list_my_families(db: Session, user_id: UUID) -> list[Family]:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    ensure_user_exists(db, user_id)
    return repository.list_families_for_user(db, user_id)


# 函数职责：校验流程，集中执行前置条件检查，失败时抛出领域异常。
# 业务边界：校验函数不应偷偷修改业务状态，便于调用方预测副作用。
def assert_user_in_family(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID,
) -> FamilyMember:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    member = repository.get_family_member(db, family_id, user_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if member is None or member.status != FamilyMemberStatus.ACTIVE:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise FamilyMemberNotFoundError("user is not an active family member")
    return member


# 函数职责：解析流程，把外部输入、自然语言或原始字段转换为系统内部标准形式。
# 业务边界：解析结果只能作为候选或标准化结果，关键写入仍需权限和业务校验。
def resolve_member_reference(
    db: Session,
    *,
    current_user_id: UUID,
    current_family_id: UUID,
    member_reference: str,
) -> MemberResolutionResult:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    assert_user_in_family(db, user_id=current_user_id, family_id=current_family_id)
    normalized = member_resolver.normalize_member_reference(member_reference)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if member_resolver.is_self_reference(normalized):
        member = assert_user_in_family(
            db,
            user_id=current_user_id,
            family_id=current_family_id,
        )
        return _resolution_from_member(member, confidence=1.0, message="已解析为本人")

    matches: list[FamilyMember] = []
    seen_ids: set[UUID] = set()
    # 循环说明：逐项处理集合中的业务对象，保持每个元素处理逻辑一致。
    for label in member_resolver.relationship_labels_for_reference(normalized):
        # 循环说明：逐项处理集合中的业务对象，保持每个元素处理逻辑一致。
        for member in repository.find_members_by_relationship_label(
            db,
            current_family_id,
            label,
        ):
            # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
            if member.id not in seen_ids:
                matches.append(member)
                seen_ids.add(member.id)
    # 循环说明：逐项处理集合中的业务对象，保持每个元素处理逻辑一致。
    for member in repository.find_members_by_display_name(
        db,
        current_family_id,
        normalized,
    ):
        # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
        if member.id not in seen_ids:
            matches.append(member)
            seen_ids.add(member.id)

    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if not matches:
        result = MemberResolutionResult(
            success=False,
            target_user_id=None,
            family_member_id=None,
            display_name=None,
            relationship_label=None,
            confidence=0.0,
            need_clarification=True,
            candidates=[],
            message="未找到匹配的家庭成员，请选择或补充成员信息。",
        )
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise MemberReferenceNotFoundError(result.message)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if len(matches) > 1:
        candidates = [_candidate_from_member(member) for member in matches]
        result = MemberResolutionResult(
            success=False,
            target_user_id=None,
            family_member_id=None,
            display_name=None,
            relationship_label=None,
            confidence=0.0,
            need_clarification=True,
            candidates=candidates,
            message="成员称呼匹配到多个家庭成员，请进一步确认。",
        )
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise MemberReferenceAmbiguousError(result.message)

    return _resolution_from_member(matches[0], confidence=0.9, message="成员解析成功")


# 函数职责：业务函数，封装 家庭成员模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def _candidate_from_member(member: FamilyMember) -> MemberCandidate:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    return MemberCandidate(
        family_member_id=member.id,
        target_user_id=member.user_id,
        display_name=member.display_name,
        relationship_label=member.relationship_label,
    )


# 函数职责：业务函数，封装 家庭成员模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def _resolution_from_member(
    member: FamilyMember,
    *,
    confidence: float,
    message: str,
) -> MemberResolutionResult:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    return MemberResolutionResult(
        success=True,
        target_user_id=member.user_id,
        family_member_id=member.id,
        display_name=member.display_name,
        relationship_label=member.relationship_label,
        confidence=confidence,
        need_clarification=False,
        candidates=[],
        message=message,
    )
