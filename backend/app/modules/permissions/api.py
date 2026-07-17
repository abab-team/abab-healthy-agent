from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id_for_demo, get_db
from app.modules.family import service as family_service
from app.modules.family.exceptions import FamilyMemberNotFoundError
from app.modules.permissions import service
from app.modules.permissions.api_schemas import (
    PermissionCheckRequest,
    PermissionCheckResponse,
    PermissionResponse,
    PermissionUpdateRequest,
    permission_check_response,
    permission_response,
)
from app.modules.permissions.exceptions import PermissionNotConfiguredError


router = APIRouter(prefix="/families/{family_id}", tags=["permissions"])


def _assert_current_member(db: Session, family_id: UUID, current_user_id: UUID) -> None:
    try:
        family_service.assert_user_in_family(db, user_id=current_user_id, family_id=family_id)
    except FamilyMemberNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="family member not found") from exc


def _assert_target_member(db: Session, family_id: UUID, target_user_id: UUID) -> None:
    try:
        family_service.assert_user_in_family(db, user_id=target_user_id, family_id=family_id)
    except FamilyMemberNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="family member not found") from exc


@router.get("/permissions", response_model=list[PermissionResponse])
def list_family_permissions(
    family_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> list[PermissionResponse]:
    _assert_current_member(db, family_id, current_user_id)
    permissions = service.list_family_share_permissions(db, family_id=family_id)
    return [permission_response(permission) for permission in permissions]


@router.get("/members/{target_user_id}/permissions", response_model=PermissionResponse)
def get_member_permissions(
    family_id: UUID,
    target_user_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> PermissionResponse:
    _assert_current_member(db, family_id, current_user_id)
    _assert_target_member(db, family_id, target_user_id)
    permission = service.get_member_share_permission(
        db,
        family_id=family_id,
        target_user_id=target_user_id,
    )
    if permission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="permission not configured")
    return permission_response(permission)


@router.patch("/members/{target_user_id}/permissions", response_model=PermissionResponse)
def update_member_permissions(
    family_id: UUID,
    target_user_id: UUID,
    payload: PermissionUpdateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> PermissionResponse:
    _assert_current_member(db, family_id, current_user_id)
    _assert_target_member(db, family_id, target_user_id)
    if target_user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="members can only update their own sharing settings")
    updates = payload.model_dump(exclude={"reason"}, exclude_none=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no permission fields provided")
    try:
        permission = service.update_share_permission(
            db,
            actor_user_id=current_user_id,
            family_id=family_id,
            target_user_id=target_user_id,
            updates=updates,
            reason=payload.reason,
        )
    except PermissionNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="permission not configured") from exc
    return permission_response(permission)


@router.post("/permissions/check", response_model=PermissionCheckResponse)
def check_member_permission(
    family_id: UUID,
    payload: PermissionCheckRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> PermissionCheckResponse:
    result = service.check_member_permission(
        db,
        current_user_id=current_user_id,
        family_id=family_id,
        target_user_id=payload.target_user_id,
        permission_type=payload.permission_type,
        action=payload.action,
    )
    return permission_check_response(result)
