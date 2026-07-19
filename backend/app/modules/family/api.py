from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id_for_demo, get_db
from app.modules.family import service
from app.modules.identity import service as identity_service
from app.modules.family.api_schemas import (
    FamilyCreateRequest,
    FamilyMemberCreateRequest,
    FamilyMemberResponse,
    FamilyResponse,
    FamilyWithOwnerResponse,
    FamilyInvitationResponse,
    JoinedFamilyResponse,
    JoinFamilyByCodeRequest,
    MemberResolutionResponse,
    ResolveMemberRequest,
    family_member_response,
    family_invitation_response,
    family_response,
    member_resolution_response,
)
from app.modules.family.exceptions import (
    FamilyMemberAlreadyExistsError,
    FamilyMemberNotFoundError,
    FamilyNotFoundError,
    InvitationNotAvailableError,
    MemberReferenceAmbiguousError,
    MemberReferenceNotFoundError,
    UserAlreadyInFamilyError,
)
from app.modules.identity.exceptions import UserNotFoundError


router = APIRouter(prefix="/families", tags=["families"])


@router.post("", response_model=FamilyWithOwnerResponse, status_code=status.HTTP_201_CREATED)
def create_family(
    payload: FamilyCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> FamilyWithOwnerResponse:
    try:
        family = service.create_family_with_owner(
            db,
            owner_user_id=current_user_id,
            family_name=payload.name,
            owner_display_name=payload.owner_display_name or "本人",
        )
        owner_member = service.assert_user_in_family(
            db,
            user_id=current_user_id,
            family_id=family.id,
        )
        invitation = service.create_invitation_code(db, family_id=family.id, inviter_user_id=current_user_id)
    except UserAlreadyInFamilyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found") from exc
    return FamilyWithOwnerResponse(
        family=family_response(family),
        owner_member=family_member_response(owner_member),
        invitation=family_invitation_response(invitation),
    )


@router.post("/join-by-code", response_model=JoinedFamilyResponse, status_code=status.HTTP_201_CREATED)
def join_family_by_code(
    payload: JoinFamilyByCodeRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> JoinedFamilyResponse:
    try:
        family, member = service.join_family_by_invitation_code(db, user_id=current_user_id, invite_code=payload.invite_code)
    except UserAlreadyInFamilyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvitationNotAvailableError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return JoinedFamilyResponse(family=family_response(family), member=family_member_response(member))


@router.post("/{family_id}/invitation-codes", response_model=FamilyInvitationResponse, status_code=status.HTTP_201_CREATED)
def create_invitation_code(
    family_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> FamilyInvitationResponse:
    try:
        invitation = service.create_invitation_code(db, family_id=family_id, inviter_user_id=current_user_id)
    except FamilyMemberNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return family_invitation_response(invitation)


@router.get("", response_model=list[FamilyResponse])
def list_my_families(
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> list[FamilyResponse]:
    try:
        families = service.list_my_families(db, current_user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found") from exc
    return [family_response(family) for family in families]


@router.get("/{family_id}/members", response_model=list[FamilyMemberResponse])
def list_family_members(
    family_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> list[FamilyMemberResponse]:
    try:
        service.assert_user_in_family(db, user_id=current_user_id, family_id=family_id)
        members = service.list_family_members(db, family_id)
    except (FamilyNotFoundError, FamilyMemberNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="family member not found",
        ) from exc
    return [
        family_member_response(
            member,
            avatar_url=(identity_service.get_user(db, member.user_id).avatar_url if identity_service.get_user(db, member.user_id) else None),
        )
        for member in members
    ]


@router.post("/{family_id}/members", response_model=FamilyMemberResponse, status_code=status.HTTP_201_CREATED)
def add_registered_member(
    family_id: UUID,
    payload: FamilyMemberCreateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> FamilyMemberResponse:
    try:
        service.assert_user_in_family(db, user_id=current_user_id, family_id=family_id)
        member = service.add_registered_member(
            db,
            family_id=family_id,
            user_id=payload.user_id,
            relationship_label=payload.relationship_label,
            display_name=payload.display_name,
            role=payload.role,
        )
    except FamilyMemberAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (FamilyNotFoundError, FamilyMemberNotFoundError, UserNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="resource not found") from exc
    return family_member_response(member)


@router.post("/{family_id}/resolve-member", response_model=MemberResolutionResponse)
def resolve_member(
    family_id: UUID,
    payload: ResolveMemberRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> MemberResolutionResponse:
    try:
        result = service.resolve_member_reference(
            db,
            current_user_id=current_user_id,
            current_family_id=family_id,
            member_reference=payload.member_reference,
        )
    except MemberReferenceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MemberReferenceAmbiguousError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except FamilyMemberNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="family member not found") from exc
    return member_resolution_response(result)
