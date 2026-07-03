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
    "can_view_memory_summary",
    "can_create_symptom_records",
    "can_create_metric_records",
    "can_upload_documents",
    "can_create_medical_events",
    "can_generate_reports",
    "can_generate_doctor_visit_summary",
    "can_export_summary",
}


def get_member_share_permission(
    db: Session,
    family_id: UUID,
    user_id: UUID,
) -> MemberSharePermission | None:
    return db.scalar(
        select(MemberSharePermission).where(
            MemberSharePermission.family_id == family_id,
            MemberSharePermission.user_id == user_id,
        ),
    )


def create_default_share_permission(
    db: Session,
    family_id: UUID,
    user_id: UUID,
    *,
    share_all: bool = True,
) -> MemberSharePermission:
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


def update_member_share_permission(
    db: Session,
    family_id: UUID,
    user_id: UUID,
    **fields: bool,
) -> MemberSharePermission | None:
    permission = get_member_share_permission(db, family_id, user_id)
    if permission is None:
        return None
    for field, value in fields.items():
        if field in PERMISSION_FIELDS:
            setattr(permission, field, value)
    db.flush()
    return permission


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


def list_permissions_for_family(
    db: Session,
    family_id: UUID,
) -> list[MemberSharePermission]:
    return list(
        db.scalars(
            select(MemberSharePermission).where(
                MemberSharePermission.family_id == family_id,
            ),
        ),
    )
