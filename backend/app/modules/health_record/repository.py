# 模块领域：健康记录模块
# 领域说明：负责症状、用药、就医、备注等事件型健康记录。
# 文件职责：仓储文件。封装数据库查询和写入细节，让业务服务只表达业务意图。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.health_data.enums import ConfidenceLevel
from app.modules.health_record.enums import (
    HealthRecordDraftStatus,
    HealthRecordDraftType,
    HealthRecordSource,
    SymptomRecordStatus,
)
from app.modules.health_record.models import HealthRecordDraft, SymptomRecord


_UNSET = object()


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def create_symptom_record(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID | None = None,
    created_by_user_id: UUID,
    raw_text: str,
    symptom_name: str | None = None,
    body_part: str | None = None,
    severity: int | None = None,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    duration_text: str | None = None,
    occurrence_time_text: str | None = None,
    possible_trigger: str | None = None,
    related_metric_types: list[str] | None = None,
    action_taken: str | None = None,
    follow_up_needed: bool = False,
    follow_up_at: datetime | None = None,
    status: SymptomRecordStatus = SymptomRecordStatus.ACTIVE,
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM,
    ai_summary: str | None = None,
    timeline_visible: bool = True,
    source: HealthRecordSource = HealthRecordSource.MANUAL,
) -> SymptomRecord:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    record = SymptomRecord(
        user_id=user_id,
        family_id=family_id,
        created_by_user_id=created_by_user_id,
        raw_text=raw_text,
        symptom_name=symptom_name,
        body_part=body_part,
        severity=severity,
        started_at=started_at,
        ended_at=ended_at,
        duration_text=duration_text,
        occurrence_time_text=occurrence_time_text,
        possible_trigger=possible_trigger,
        related_metric_types=related_metric_types,
        action_taken=action_taken,
        follow_up_needed=follow_up_needed,
        follow_up_at=follow_up_at,
        status=status,
        confidence_level=confidence_level,
        ai_summary=ai_summary,
        timeline_visible=timeline_visible,
        source=source,
    )
    db.add(record)
    db.flush()
    return record


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_symptom_record(db: Session, record_id: UUID) -> SymptomRecord | None:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    return db.get(SymptomRecord, record_id)


# 函数职责：列表查询流程，按过滤条件返回一组对象，并保持排序、分页或范围语义稳定。
# 业务边界：返回集合时要避免把未授权数据暴露给调用方。
def list_symptom_records(
    db: Session,
    user_id: UUID,
    *,
    family_id: UUID | None | object = _UNSET,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    status: SymptomRecordStatus | None = None,
    limit: int = 100,
) -> list[SymptomRecord]:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    stmt = select(SymptomRecord).where(SymptomRecord.user_id == user_id)
    if family_id is not _UNSET:
        stmt = stmt.where(SymptomRecord.family_id == family_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if start_at is not None:
        stmt = stmt.where(SymptomRecord.started_at >= start_at)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if end_at is not None:
        stmt = stmt.where(SymptomRecord.started_at <= end_at)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if status is not None:
        stmt = stmt.where(SymptomRecord.status == status)
    return list(db.scalars(stmt.order_by(SymptomRecord.created_at.desc()).limit(limit)))


# 函数职责：列表查询流程，按过滤条件返回一组对象，并保持排序、分页或范围语义稳定。
# 业务边界：返回集合时要避免把未授权数据暴露给调用方。
def list_recent_symptom_records(
    db: Session,
    user_id: UUID,
    *,
    family_id: UUID | None | object = _UNSET,
    days: int = 30,
    limit: int = 50,
) -> list[SymptomRecord]:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    start_at = datetime.now(timezone.utc) - timedelta(days=days)
    return list_symptom_records(db, user_id, family_id=family_id, start_at=start_at, limit=limit)


# 函数职责：列表查询流程，按过滤条件返回一组对象，并保持排序、分页或范围语义稳定。
# 业务边界：返回集合时要避免把未授权数据暴露给调用方。
def list_follow_up_symptoms(
    db: Session,
    user_id: UUID,
    *,
    family_id: UUID | None | object = _UNSET,
    due_before: datetime | None = None,
) -> list[SymptomRecord]:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    stmt = select(SymptomRecord).where(
        SymptomRecord.user_id == user_id,
        SymptomRecord.follow_up_needed.is_(True),
    )
    if family_id is not _UNSET:
        stmt = stmt.where(SymptomRecord.family_id == family_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if due_before is not None:
        stmt = stmt.where(SymptomRecord.follow_up_at <= due_before)
    return list(db.scalars(stmt.order_by(SymptomRecord.follow_up_at.asc())))


# 函数职责：更新流程，在校验当前状态后修改已有对象或推进状态机。
# 业务边界：更新动作要保持幂等性和状态合法性，避免跳过必要确认。
def update_symptom_record_status(
    db: Session,
    record_id: UUID,
    status: SymptomRecordStatus,
) -> SymptomRecord | None:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    record = get_symptom_record(db, record_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if record is None:
        return None
    record.status = status
    db.flush()
    return record


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def create_health_record_draft(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID | None = None,
    created_by_user_id: UUID,
    target_display_name: str | None = None,
    raw_text: str,
    draft_type: HealthRecordDraftType,
    extracted_json: dict,
    missing_fields: list[str] | None = None,
    safety_flags: list[str] | None = None,
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM,
    status: HealthRecordDraftStatus = HealthRecordDraftStatus.PENDING,
    expires_at: datetime | None = None,
) -> HealthRecordDraft:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    draft = HealthRecordDraft(
        user_id=user_id,
        family_id=family_id,
        created_by_user_id=created_by_user_id,
        target_display_name=target_display_name,
        raw_text=raw_text,
        draft_type=draft_type,
        extracted_json=extracted_json,
        missing_fields=missing_fields,
        safety_flags=safety_flags,
        confidence_level=confidence_level,
        status=status,
        expires_at=expires_at,
    )
    db.add(draft)
    db.flush()
    return draft


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_health_record_draft(
    db: Session,
    draft_id: UUID,
) -> HealthRecordDraft | None:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    return db.get(HealthRecordDraft, draft_id)


# 函数职责：列表查询流程，按过滤条件返回一组对象，并保持排序、分页或范围语义稳定。
# 业务边界：返回集合时要避免把未授权数据暴露给调用方。
def list_pending_drafts(
    db: Session,
    user_id: UUID,
    *,
    family_id: UUID | None | object = _UNSET,
    limit: int = 50,
) -> list[HealthRecordDraft]:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    stmt = select(HealthRecordDraft).where(
        HealthRecordDraft.user_id == user_id,
        HealthRecordDraft.status == HealthRecordDraftStatus.PENDING,
    )
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if family_id is not _UNSET:
        stmt = stmt.where(HealthRecordDraft.family_id == family_id)
    return list(db.scalars(stmt.order_by(HealthRecordDraft.created_at.desc()).limit(limit)))


# 函数职责：更新流程，在校验当前状态后修改已有对象或推进状态机。
# 业务边界：更新动作要保持幂等性和状态合法性，避免跳过必要确认。
def update_draft_status(
    db: Session,
    draft_id: UUID,
    status: HealthRecordDraftStatus,
    *,
    confirmed_at: datetime | None = None,
    confirmed_record_id: UUID | None = None,
) -> HealthRecordDraft | None:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    draft = get_health_record_draft(db, draft_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if draft is None:
        return None
    draft.status = status
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if confirmed_at is not None:
        draft.confirmed_at = confirmed_at
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if confirmed_record_id is not None:
        draft.confirmed_record_id = confirmed_record_id
    db.flush()
    return draft
