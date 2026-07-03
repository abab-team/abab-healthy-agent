# 模块领域：健康档案模块
# 领域说明：负责家庭成员基础健康信息、长期档案摘要和健康画像。
# 文件职责：数据结构文件。定义服务层/API 的输入输出对象，隔离外部请求与内部 ORM 模型。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.modules.health_profile.enums import BloodType
from app.modules.health_profile.models import HealthProfile
from app.modules.identity.enums import Gender


# 类职责：HealthProfileSnapshot 是 健康档案模块 的数据传输结构，用于接口入参、出参或服务层结果。
# 设计边界：Schema 负责数据形状和校验，不直接访问数据库。
@dataclass(frozen=True)
class HealthProfileSnapshot:
    # 字段说明：user_id 是接口/服务层数据结构中的一个显式字段。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    user_id: UUID
    # 字段说明：height_cm 是接口/服务层数据结构中的一个显式字段。
    height_cm: float | None
    # 字段说明：gender 是接口/服务层数据结构中的一个显式字段。
    gender: Gender | None
    # 字段说明：birth_date 是接口/服务层数据结构中的一个显式字段。
    birth_date: date | None
    # 字段说明：blood_type 是接口/服务层数据结构中的一个显式字段。
    blood_type: BloodType | None
    # 字段说明：health_goal 是接口/服务层数据结构中的一个显式字段。
    health_goal: str | None
    # 字段说明：chronic_conditions_summary 是接口/服务层数据结构中的一个显式字段。
    chronic_conditions_summary: str | None
    # 字段说明：allergy_summary 是接口/服务层数据结构中的一个显式字段。
    allergy_summary: str | None
    # 字段说明：medication_summary 是接口/服务层数据结构中的一个显式字段。
    medication_summary: str | None


# 函数职责：业务函数，封装 健康档案模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def to_profile_snapshot(profile: HealthProfile) -> HealthProfileSnapshot:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return HealthProfileSnapshot(
        user_id=profile.user_id,
        height_cm=float(profile.height_cm) if profile.height_cm is not None else None,
        gender=profile.gender,
        birth_date=profile.birth_date,
        blood_type=profile.blood_type,
        health_goal=profile.health_goal,
        chronic_conditions_summary=profile.chronic_conditions_summary,
        allergy_summary=profile.allergy_summary,
        medication_summary=profile.medication_summary,
    )
