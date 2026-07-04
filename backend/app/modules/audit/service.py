from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.audit.enums import DataAccessAction, DataAccessCategory
from app.modules.audit.models import DataAccessLog
from app.modules.audit import repository


SAFE_PERMISSION_RESULT_FIELDS = {
    "allowed",
    "permission_type",
    "action",
    "reason",
    "visibility_scope",
}


def log_data_access(
    db: Session,
    *,
    request_id: str | None = None,
    actor_user_id: UUID | None = None,
    family_id: UUID | None = None,
    target_user_id: UUID | None = None,
    data_category: DataAccessCategory | str,
    action: DataAccessAction | str,
    access_reason: str | None = None,
    allowed: bool,
    permission_result: dict | None = None,
    resource_type: str | None = None,
    resource_id: UUID | None = None,
) -> DataAccessLog:
    return repository.create_data_access_log(
        db,
        request_id=request_id,
        actor_user_id=actor_user_id,
        family_id=family_id,
        target_user_id=target_user_id,
        data_category=data_category,
        action=action,
        access_reason=access_reason,
        allowed=allowed,
        permission_result=_safe_permission_result(permission_result),
        resource_type=resource_type,
        resource_id=resource_id,
    )


def list_data_access_logs(
    db: Session,
    *,
    actor_user_id: UUID | None = None,
    target_user_id: UUID | None = None,
    family_id: UUID | None = None,
    data_category: DataAccessCategory | str | None = None,
    allowed: bool | None = None,
    limit: int = 100,
) -> list[DataAccessLog]:
    return repository.list_data_access_logs(
        db,
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        family_id=family_id,
        data_category=data_category,
        allowed=allowed,
        limit=limit,
    )


def _safe_permission_result(permission_result: dict | None) -> dict | None:
    if permission_result is None:
        return None
    return {
        key: permission_result[key]
        for key in SAFE_PERMISSION_RESULT_FIELDS
        if key in permission_result
    }
