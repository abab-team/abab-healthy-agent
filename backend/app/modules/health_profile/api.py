from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.access_control import require_self_or_family_permission
from app.api.deps import get_current_user_id_for_demo, get_db
from app.modules.health_profile import service
from app.modules.health_profile.api_schemas import (
    HealthProfileResponse,
    HealthProfileUpdateRequest,
)


router = APIRouter(tags=["health-profile"])


@router.get("/health-profile/me", response_model=HealthProfileResponse)
def get_my_health_profile(
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    require_self_or_family_permission(
        db=db,
        current_user_id=current_user_id,
        target_user_id=current_user_id,
        permission_type="profile",
        action="view",
        data_category="profile",
        access_reason="api_health_profile_self",
    )
    return _profile_response(service.ensure_profile(db, current_user_id))


@router.patch("/health-profile/me", response_model=HealthProfileResponse)
def update_my_health_profile(
    payload: HealthProfileUpdateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    profile = service.create_or_update_profile(
        db,
        current_user_id,
        payload.model_dump(exclude_unset=True),
    )
    return _profile_response(profile)


@router.get(
    "/families/{family_id}/members/{target_user_id}/health-profile",
    response_model=HealthProfileResponse,
)
def get_family_member_health_profile(
    family_id: UUID,
    target_user_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
):
    _require_permission(
        db,
        current_user_id=current_user_id,
        family_id=family_id,
        target_user_id=target_user_id,
        permission_type="profile",
        action="view",
    )
    return _profile_response(service.ensure_profile(db, target_user_id))


def _require_permission(
    db: Session,
    *,
    current_user_id: UUID,
    family_id: UUID,
    target_user_id: UUID,
    permission_type: str,
    action: str,
) -> None:
    require_self_or_family_permission(
        db,
        current_user_id=current_user_id,
        family_id=family_id,
        target_user_id=target_user_id,
        permission_type=permission_type,
        action=action,
        data_category="profile",
        access_reason="api_health_profile",
    )


def _profile_response(profile) -> dict:
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "height_cm": _float_or_none(profile.height_cm),
        "gender": _enum_value(profile.gender),
        "birth_date": profile.birth_date,
        "blood_type": _enum_value(profile.blood_type),
        "health_goal": profile.health_goal,
        "chronic_conditions_summary": profile.chronic_conditions_summary,
        "allergy_summary": profile.allergy_summary,
        "medication_summary": profile.medication_summary,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }


def _enum_value(value):
    return value.value if hasattr(value, "value") else value


def _float_or_none(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return value
