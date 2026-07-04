from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.enums import DataAccessAction, DataAccessCategory
from app.modules.audit.models import DataAccessLog


def create_data_access_log(
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
    log = DataAccessLog(
        request_id=request_id,
        actor_user_id=actor_user_id,
        family_id=family_id,
        target_user_id=target_user_id,
        data_category=_coerce_enum(DataAccessCategory, data_category),
        action=_coerce_enum(DataAccessAction, action),
        access_reason=access_reason,
        allowed=allowed,
        permission_result=permission_result,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    db.add(log)
    db.flush()
    return log


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
    stmt = select(DataAccessLog)
    if actor_user_id is not None:
        stmt = stmt.where(DataAccessLog.actor_user_id == actor_user_id)
    if target_user_id is not None:
        stmt = stmt.where(DataAccessLog.target_user_id == target_user_id)
    if family_id is not None:
        stmt = stmt.where(DataAccessLog.family_id == family_id)
    if data_category is not None:
        stmt = stmt.where(DataAccessLog.data_category == _coerce_enum(DataAccessCategory, data_category))
    if allowed is not None:
        stmt = stmt.where(DataAccessLog.allowed.is_(allowed))
    return list(db.scalars(stmt.order_by(DataAccessLog.created_at.desc()).limit(limit)))


def _coerce_enum(enum_cls, value):
    if isinstance(value, enum_cls):
        return value
    return enum_cls(value)
