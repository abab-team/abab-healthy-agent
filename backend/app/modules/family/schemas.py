# 模块领域：家庭成员模块
# 领域说明：负责家庭、成员关系、邀请流程和自然语言成员称呼解析。
# 文件职责：数据结构文件。定义服务层/API 的输入输出对象，隔离外部请求与内部 ORM 模型。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


# 类职责：MemberCandidate 是 家庭成员模块 的数据传输结构，用于接口入参、出参或服务层结果。
# 设计边界：Schema 负责数据形状和校验，不直接访问数据库。
@dataclass(frozen=True)
class MemberCandidate:
    # 字段说明：family_member_id 是接口/服务层数据结构中的一个显式字段。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    family_member_id: UUID
    # 字段说明：target_user_id 是接口/服务层数据结构中的一个显式字段。
    target_user_id: UUID
    # 字段说明：display_name 是接口/服务层数据结构中的一个显式字段。
    display_name: str | None
    # 字段说明：relationship_label 是接口/服务层数据结构中的一个显式字段。
    relationship_label: str | None


# 类职责：MemberResolutionResult 是 家庭成员模块 的数据传输结构，用于接口入参、出参或服务层结果。
# 设计边界：Schema 负责数据形状和校验，不直接访问数据库。
@dataclass(frozen=True)
class MemberResolutionResult:
    # 字段说明：success 是接口/服务层数据结构中的一个显式字段。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    success: bool
    # 字段说明：target_user_id 是接口/服务层数据结构中的一个显式字段。
    target_user_id: UUID | None
    # 字段说明：family_member_id 是接口/服务层数据结构中的一个显式字段。
    family_member_id: UUID | None
    # 字段说明：display_name 是接口/服务层数据结构中的一个显式字段。
    display_name: str | None
    # 字段说明：relationship_label 是接口/服务层数据结构中的一个显式字段。
    relationship_label: str | None
    # 字段说明：confidence 是接口/服务层数据结构中的一个显式字段。
    confidence: float
    # 字段说明：need_clarification 是接口/服务层数据结构中的一个显式字段。
    need_clarification: bool
    # 字段说明：candidates 是接口/服务层数据结构中的一个显式字段。
    candidates: list[MemberCandidate]
    # 字段说明：message 是接口/服务层数据结构中的一个显式字段。
    message: str
