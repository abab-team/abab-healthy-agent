# 模块领域：健康档案模块
# 领域说明：负责家庭成员基础健康信息、长期档案摘要和健康画像。
# 文件职责：业务服务文件。编排领域规则、权限校验、仓储调用和状态流转，是模块的主要业务入口。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.health_profile import repository
from app.modules.health_profile.exceptions import HealthProfileNotFoundError
from app.modules.health_profile.models import HealthProfile
from app.modules.health_profile.schemas import HealthProfileSnapshot, to_profile_snapshot


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_profile(db: Session, user_id: UUID) -> HealthProfile | None:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    return repository.get_profile_by_user_id(db, user_id)


# 函数职责：校验流程，集中执行前置条件检查，失败时抛出领域异常。
# 业务边界：校验函数不应偷偷修改业务状态，便于调用方预测副作用。
def ensure_profile(db: Session, user_id: UUID) -> HealthProfile:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    return repository.get_or_create_profile(db, user_id)


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def create_or_update_profile(
    db: Session,
    user_id: UUID,
    fields: dict,
) -> HealthProfile:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    profile = repository.get_profile_by_user_id(db, user_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if profile is None:
        return repository.create_profile(db, user_id=user_id, **fields)
    updated = repository.update_profile(db, user_id, **fields)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if updated is None:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise HealthProfileNotFoundError("health profile not found")
    return updated


# 函数职责：更新流程，在校验当前状态后修改已有对象或推进状态机。
# 业务边界：更新动作要保持幂等性和状态合法性，避免跳过必要确认。
def update_health_goal(
    db: Session,
    user_id: UUID,
    health_goal: str,
) -> HealthProfile:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    return create_or_update_profile(db, user_id, {"health_goal": health_goal})


# 函数职责：更新流程，在校验当前状态后修改已有对象或推进状态机。
# 业务边界：更新动作要保持幂等性和状态合法性，避免跳过必要确认。
def update_profile_summaries(
    db: Session,
    user_id: UUID,
    *,
    chronic_conditions_summary: str | None = None,
    allergy_summary: str | None = None,
    medication_summary: str | None = None,
) -> HealthProfile:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    fields = {
        "chronic_conditions_summary": chronic_conditions_summary,
        "allergy_summary": allergy_summary,
        "medication_summary": medication_summary,
    }
    return create_or_update_profile(
        db,
        user_id,
        {key: value for key, value in fields.items() if value is not None},
    )


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_profile_snapshot(db: Session, user_id: UUID) -> HealthProfileSnapshot:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    profile = ensure_profile(db, user_id)
    return to_profile_snapshot(profile)
