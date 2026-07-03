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


def create_family_with_owner(
    db: Session,
    *,
    owner_user_id: UUID,
    family_name: str,
    owner_display_name: str = "本人",
) -> Family:
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


def add_registered_member(
    db: Session,
    *,
    family_id: UUID,
    user_id: UUID,
    relationship_label: str,
    display_name: str,
    role: FamilyRole = FamilyRole.MEMBER,
) -> FamilyMember:
    if repository.get_family_by_id(db, family_id) is None:
        raise FamilyNotFoundError("family not found")
    ensure_user_exists(db, user_id)
    if repository.get_family_member(db, family_id, user_id) is not None:
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


def list_family_members(db: Session, family_id: UUID) -> list[FamilyMember]:
    if repository.get_family_by_id(db, family_id) is None:
        raise FamilyNotFoundError("family not found")
    return repository.list_family_members(db, family_id)


def list_my_families(db: Session, user_id: UUID) -> list[Family]:
    ensure_user_exists(db, user_id)
    return repository.list_families_for_user(db, user_id)


def assert_user_in_family(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID,
) -> FamilyMember:
    member = repository.get_family_member(db, family_id, user_id)
    if member is None or member.status != FamilyMemberStatus.ACTIVE:
        raise FamilyMemberNotFoundError("user is not an active family member")
    return member


def resolve_member_reference(
    db: Session,
    *,
    current_user_id: UUID,
    current_family_id: UUID,
    member_reference: str,
) -> MemberResolutionResult:
    assert_user_in_family(db, user_id=current_user_id, family_id=current_family_id)
    normalized = member_resolver.normalize_member_reference(member_reference)
    if member_resolver.is_self_reference(normalized):
        member = assert_user_in_family(
            db,
            user_id=current_user_id,
            family_id=current_family_id,
        )
        return _resolution_from_member(member, confidence=1.0, message="已解析为本人")

    matches: list[FamilyMember] = []
    seen_ids: set[UUID] = set()
    for label in member_resolver.relationship_labels_for_reference(normalized):
        for member in repository.find_members_by_relationship_label(
            db,
            current_family_id,
            label,
        ):
            if member.id not in seen_ids:
                matches.append(member)
                seen_ids.add(member.id)
    for member in repository.find_members_by_display_name(
        db,
        current_family_id,
        normalized,
    ):
        if member.id not in seen_ids:
            matches.append(member)
            seen_ids.add(member.id)

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
        raise MemberReferenceNotFoundError(result.message)
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
        raise MemberReferenceAmbiguousError(result.message)

    return _resolution_from_member(matches[0], confidence=0.9, message="成员解析成功")


def _candidate_from_member(member: FamilyMember) -> MemberCandidate:
    return MemberCandidate(
        family_member_id=member.id,
        target_user_id=member.user_id,
        display_name=member.display_name,
        relationship_label=member.relationship_label,
    )


def _resolution_from_member(
    member: FamilyMember,
    *,
    confidence: float,
    message: str,
) -> MemberResolutionResult:
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
