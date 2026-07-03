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


def create_family(db: Session, *, name: str, owner_user_id: UUID) -> Family:
    family = Family(name=name, owner_user_id=owner_user_id)
    db.add(family)
    db.flush()
    return family


def get_family_by_id(db: Session, family_id: UUID) -> Family | None:
    return db.get(Family, family_id)


def list_families_for_user(db: Session, user_id: UUID) -> list[Family]:
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


def get_family_member(
    db: Session,
    family_id: UUID,
    user_id: UUID,
) -> FamilyMember | None:
    return db.scalar(
        select(FamilyMember).where(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == user_id,
        ),
    )


def list_family_members(db: Session, family_id: UUID) -> list[FamilyMember]:
    return list(
        db.scalars(
            select(FamilyMember).where(FamilyMember.family_id == family_id),
        ),
    )


def find_members_by_relationship_label(
    db: Session,
    family_id: UUID,
    relationship_label: str,
) -> list[FamilyMember]:
    return list(
        db.scalars(
            select(FamilyMember).where(
                FamilyMember.family_id == family_id,
                FamilyMember.relationship_label == relationship_label,
                FamilyMember.status == FamilyMemberStatus.ACTIVE,
            ),
        ),
    )


def find_members_by_display_name(
    db: Session,
    family_id: UUID,
    display_name: str,
) -> list[FamilyMember]:
    return list(
        db.scalars(
            select(FamilyMember).where(
                FamilyMember.family_id == family_id,
                FamilyMember.display_name == display_name,
                FamilyMember.status == FamilyMemberStatus.ACTIVE,
            ),
        ),
    )


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


def get_invitation_by_code(
    db: Session,
    invite_code: str,
) -> FamilyInvitation | None:
    return db.scalar(
        select(FamilyInvitation).where(FamilyInvitation.invite_code == invite_code),
    )
