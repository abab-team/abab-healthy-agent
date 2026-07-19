from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.api.validators import DisplayName, Name, RequiredDisplayName, RequiredRelationshipLabel, RequiredShortText, STRICT_MODEL_CONFIG
from app.modules.family.enums import FamilyMemberStatus, FamilyRole
from app.modules.family.models import Family, FamilyInvitation, FamilyMember
from app.modules.family.schemas import MemberResolutionResult


class FamilyCreateRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    name: Name
    owner_display_name: DisplayName = None


class FamilyResponse(BaseModel):
    id: UUID
    name: str
    owner_user_id: UUID
    created_at: datetime
    updated_at: datetime


class FamilyMemberCreateRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    user_id: UUID
    relationship_label: RequiredRelationshipLabel
    display_name: RequiredDisplayName
    role: FamilyRole = FamilyRole.MEMBER


class FamilyMemberResponse(BaseModel):
    id: UUID
    family_id: UUID
    user_id: UUID
    role: FamilyRole
    relationship_label: str | None
    display_name: str | None
    status: FamilyMemberStatus
    joined_at: datetime
    created_at: datetime
    updated_at: datetime
    avatar_url: str | None = None


class FamilyInvitationResponse(BaseModel):
    id: UUID
    family_id: UUID
    invite_code: str
    status: str
    expires_at: datetime


class JoinFamilyByCodeRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    invite_code: RequiredShortText


class JoinedFamilyResponse(BaseModel):
    family: FamilyResponse
    member: FamilyMemberResponse


class FamilyWithOwnerResponse(BaseModel):
    family: FamilyResponse
    owner_member: FamilyMemberResponse
    invitation: FamilyInvitationResponse


class ResolveMemberRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    member_reference: Name


class MemberCandidateResponse(BaseModel):
    family_member_id: UUID
    target_user_id: UUID
    display_name: str | None
    relationship_label: str | None


class MemberResolutionResponse(BaseModel):
    success: bool
    target_user_id: UUID | None
    family_member_id: UUID | None
    display_name: str | None
    relationship_label: str | None
    confidence: float
    need_clarification: bool
    candidates: list[MemberCandidateResponse]
    message: str


def family_response(family: Family) -> FamilyResponse:
    return FamilyResponse(
        id=family.id,
        name=family.name,
        owner_user_id=family.owner_user_id,
        created_at=family.created_at,
        updated_at=family.updated_at,
    )


def family_member_response(member: FamilyMember, *, avatar_url: str | None = None) -> FamilyMemberResponse:
    return FamilyMemberResponse(
        id=member.id,
        family_id=member.family_id,
        user_id=member.user_id,
        role=member.role,
        relationship_label=member.relationship_label,
        display_name=member.display_name,
        status=member.status,
        joined_at=member.joined_at,
        created_at=member.created_at,
        updated_at=member.updated_at,
        avatar_url=avatar_url,
    )


def family_invitation_response(invitation: FamilyInvitation) -> FamilyInvitationResponse:
    return FamilyInvitationResponse(
        id=invitation.id,
        family_id=invitation.family_id,
        invite_code=invitation.invite_code,
        status=invitation.status.value,
        expires_at=invitation.expires_at,
    )


def member_resolution_response(result: MemberResolutionResult) -> MemberResolutionResponse:
    return MemberResolutionResponse(
        success=result.success,
        target_user_id=result.target_user_id,
        family_member_id=result.family_member_id,
        display_name=result.display_name,
        relationship_label=result.relationship_label,
        confidence=result.confidence,
        need_clarification=result.need_clarification,
        candidates=[
            MemberCandidateResponse(
                family_member_id=candidate.family_member_id,
                target_user_id=candidate.target_user_id,
                display_name=candidate.display_name,
                relationship_label=candidate.relationship_label,
            )
            for candidate in result.candidates
        ],
        message=result.message,
    )
