# 模块领域：健康记录模块
# 领域说明：负责症状、用药、就医、备注等事件型健康记录。
# 文件职责：业务服务文件。编排领域规则、权限校验、仓储调用和状态流转，是模块的主要业务入口。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.health_data.enums import ConfidenceLevel
from app.modules.health_record import draft_parser, repository
from app.modules.health_record.enums import (
    HealthRecordDraftStatus,
    HealthRecordDraftType,
    HealthRecordSource,
    SymptomRecordStatus,
)
from app.modules.health_record.exceptions import (
    HealthRecordDraftNotFoundError,
    HealthRecordDraftNotPendingError,
    HealthRecordDraftTypeUnsupportedError,
    InvalidHealthRecordDraftError,
    SymptomRecordNotFoundError,
)
from app.modules.health_record.models import HealthRecordDraft, SymptomRecord
from app.modules.health_record.schemas import SymptomSummary


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def create_symptom_record(
    db: Session,
    *,
    user_id: UUID,
    created_by_user_id: UUID,
    raw_text: str,
    family_id: UUID | None = None,
    symptom_name: str | None = None,
    body_part: str | None = None,
    severity: int | None = None,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    possible_trigger: str | None = None,
    follow_up_needed: bool = False,
    follow_up_at: datetime | None = None,
    ai_summary: str | None = None,
    source: HealthRecordSource | str = HealthRecordSource.MANUAL,
) -> SymptomRecord:
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    if not raw_text or not raw_text.strip():
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise InvalidHealthRecordDraftError("raw_text is required")
    return repository.create_symptom_record(
        db,
        user_id=user_id,
        family_id=family_id,
        created_by_user_id=created_by_user_id,
        raw_text=raw_text.strip(),
        symptom_name=symptom_name,
        body_part=body_part,
        severity=severity,
        started_at=started_at or datetime.now(timezone.utc),
        ended_at=ended_at,
        possible_trigger=possible_trigger,
        follow_up_needed=follow_up_needed,
        follow_up_at=follow_up_at,
        confidence_level=ConfidenceLevel.MEDIUM,
        ai_summary=ai_summary,
        timeline_visible=True,
        source=_coerce_enum(HealthRecordSource, source),
    )


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_recent_symptoms(
    db: Session,
    *,
    user_id: UUID,
    days: int = 30,
) -> list[SymptomRecord]:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    return repository.list_recent_symptom_records(db, user_id, days=days)


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_symptom_summary(
    db: Session,
    *,
    user_id: UUID,
    days: int = 30,
) -> SymptomSummary:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    records = get_recent_symptoms(db, user_id=user_id, days=days)
    active_count = sum(1 for record in records if record.status == SymptomRecordStatus.ACTIVE)
    follow_up_count = sum(1 for record in records if record.follow_up_needed)
    names = Counter(record.symptom_name for record in records if record.symptom_name)
    return SymptomSummary(
        days=days,
        count=len(records),
        active_count=active_count,
        follow_up_needed_count=follow_up_count,
        latest_record=_record_dict(records[0]) if records else None,
        common_symptoms=[
            {"symptom_name": name, "count": count}
            for name, count in names.most_common()
        ],
        records=[_record_dict(record) for record in records],
    )


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def create_health_record_draft(
    db: Session,
    *,
    user_id: UUID,
    created_by_user_id: UUID,
    raw_text: str,
    family_id: UUID | None = None,
    target_display_name: str | None = None,
    draft_type: HealthRecordDraftType | str = HealthRecordDraftType.SYMPTOM,
    extracted_json: dict | None = None,
    missing_fields: list[str] | None = None,
    safety_flags: list[str] | None = None,
    confidence_level: ConfidenceLevel | str = ConfidenceLevel.MEDIUM,
) -> HealthRecordDraft:
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    if not raw_text or not raw_text.strip():
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise InvalidHealthRecordDraftError("raw_text is required")
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if extracted_json is None:
        extracted_json = {}
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if not isinstance(extracted_json, dict):
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise InvalidHealthRecordDraftError("extracted_json must be a dict")
    return repository.create_health_record_draft(
        db,
        user_id=user_id,
        family_id=family_id,
        created_by_user_id=created_by_user_id,
        target_display_name=target_display_name,
        raw_text=raw_text.strip(),
        draft_type=_coerce_enum(HealthRecordDraftType, draft_type),
        extracted_json=extracted_json,
        missing_fields=missing_fields,
        safety_flags=safety_flags,
        confidence_level=_coerce_enum(ConfidenceLevel, confidence_level),
        status=HealthRecordDraftStatus.PENDING,
    )


# 函数职责：更新流程，在校验当前状态后修改已有对象或推进状态机。
# 业务边界：更新动作要保持幂等性和状态合法性，避免跳过必要确认。
def confirm_symptom_draft(
    db: Session,
    *,
    draft_id: UUID,
    confirmed_by_user_id: UUID,
) -> SymptomRecord:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    draft = repository.get_health_record_draft(db, draft_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if draft is None:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise HealthRecordDraftNotFoundError("health record draft not found")
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if draft.status != HealthRecordDraftStatus.PENDING:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise HealthRecordDraftNotPendingError("only pending drafts can be confirmed")
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if draft.draft_type not in {
        HealthRecordDraftType.SYMPTOM,
        HealthRecordDraftType.MIXED_HEALTH_RECORD,
    }:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise HealthRecordDraftTypeUnsupportedError("draft type cannot create symptom record")
    fields = draft_parser.symptom_fields_from_draft(draft.extracted_json)
    record = repository.create_symptom_record(
        db,
        user_id=draft.user_id,
        family_id=draft.family_id,
        created_by_user_id=confirmed_by_user_id,
        raw_text=draft.raw_text,
        symptom_name=fields["symptom_name"],
        body_part=fields["body_part"],
        severity=fields["severity"],
        duration_text=fields["duration_text"],
        occurrence_time_text=fields["occurrence_time_text"],
        possible_trigger=fields["possible_trigger"],
        related_metric_types=fields["related_metric_types"],
        action_taken=fields["action_taken"],
        follow_up_needed=fields["follow_up_needed"],
        confidence_level=draft.confidence_level,
        ai_summary=fields["ai_summary"],
        source=HealthRecordSource.AI_EXTRACTED,
    )
    repository.update_draft_status(
        db,
        draft.id,
        HealthRecordDraftStatus.CONFIRMED,
        confirmed_at=datetime.now(timezone.utc),
        confirmed_record_id=record.id,
    )
    return record


# 函数职责：业务函数，封装 健康记录模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def cancel_draft(db: Session, draft_id: UUID) -> HealthRecordDraft:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    draft = repository.update_draft_status(
        db,
        draft_id,
        HealthRecordDraftStatus.CANCELLED,
    )
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if draft is None:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise HealthRecordDraftNotFoundError("health record draft not found")
    return draft


# 函数职责：更新流程，在校验当前状态后修改已有对象或推进状态机。
# 业务边界：更新动作要保持幂等性和状态合法性，避免跳过必要确认。
def update_symptom_record_status(
    db: Session,
    record_id: UUID,
    status: SymptomRecordStatus | str,
) -> SymptomRecord:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    record = repository.update_symptom_record_status(
        db,
        record_id,
        _coerce_enum(SymptomRecordStatus, status),
    )
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if record is None:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise SymptomRecordNotFoundError("symptom record not found")
    return record


# 函数职责：业务函数，封装 健康记录模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def _coerce_enum(enum_cls: type[StrEnum], value):
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    if isinstance(value, enum_cls):
        return value
    return enum_cls(value)


# 函数职责：业务函数，封装 健康记录模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def _record_dict(record: SymptomRecord) -> dict:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    return {
        "id": str(record.id),
        "symptom_name": record.symptom_name,
        "body_part": record.body_part,
        "follow_up_needed": record.follow_up_needed,
        "status": record.status.value,
        "started_at": record.started_at,
        "created_at": record.created_at,
    }
