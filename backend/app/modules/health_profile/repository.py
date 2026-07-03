# 模块领域：健康档案模块
# 领域说明：负责家庭成员基础健康信息、长期档案摘要和健康画像。
# 文件职责：仓储文件。封装数据库查询和写入细节，让业务服务只表达业务意图。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.health_profile.enums import BloodType
from app.modules.health_profile.models import HealthProfile
from app.modules.identity.enums import Gender


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_profile_by_user_id(db: Session, user_id: UUID) -> HealthProfile | None:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    return db.scalar(select(HealthProfile).where(HealthProfile.user_id == user_id))


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def create_profile(
    db: Session,
    *,
    user_id: UUID,
    height_cm: float | None = None,
    gender: Gender | None = None,
    birth_date: date | None = None,
    blood_type: BloodType | None = None,
    health_goal: str | None = None,
    chronic_conditions_summary: str | None = None,
    allergy_summary: str | None = None,
    medication_summary: str | None = None,
) -> HealthProfile:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    profile = HealthProfile(
        user_id=user_id,
        height_cm=height_cm,
        gender=gender,
        birth_date=birth_date,
        blood_type=blood_type,
        health_goal=health_goal,
        chronic_conditions_summary=chronic_conditions_summary,
        allergy_summary=allergy_summary,
        medication_summary=medication_summary,
    )
    db.add(profile)
    db.flush()
    return profile


# 函数职责：更新流程，在校验当前状态后修改已有对象或推进状态机。
# 业务边界：更新动作要保持幂等性和状态合法性，避免跳过必要确认。
def update_profile(db: Session, user_id: UUID, **fields: object) -> HealthProfile | None:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    profile = get_profile_by_user_id(db, user_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if profile is None:
        return None
    allowed = {
        "height_cm",
        "gender",
        "birth_date",
        "blood_type",
        "health_goal",
        "chronic_conditions_summary",
        "allergy_summary",
        "medication_summary",
    }
    # 循环说明：逐项处理集合中的业务对象，保持每个元素处理逻辑一致。
    for field, value in fields.items():
        # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
        if field in allowed:
            setattr(profile, field, value)
    db.flush()
    return profile


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_or_create_profile(
    db: Session,
    user_id: UUID,
    **defaults: object,
) -> HealthProfile:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    profile = get_profile_by_user_id(db, user_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if profile is not None:
        return profile
    return create_profile(db, user_id=user_id, **defaults)


# 函数职责：列表查询流程，按过滤条件返回一组对象，并保持排序、分页或范围语义稳定。
# 业务边界：返回集合时要避免把未授权数据暴露给调用方。
def list_profiles_by_user_ids(
    db: Session,
    user_ids: list[UUID],
) -> list[HealthProfile]:
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    if not user_ids:
        return []
    return list(
        db.scalars(select(HealthProfile).where(HealthProfile.user_id.in_(user_ids))),
    )
