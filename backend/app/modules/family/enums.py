# 模块领域：家庭成员模块
# 领域说明：负责家庭、成员关系、邀请流程和自然语言成员称呼解析。
# 文件职责：枚举定义文件。集中约束状态、类型、来源等固定取值，避免魔法字符串散落在业务代码中。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from enum import StrEnum


# 类职责：FamilyRole 约束 家庭成员模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class FamilyRole(StrEnum):
    # 枚举说明：OWNER 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    OWNER = "owner"
    # 枚举说明：ADMIN 是该枚举允许出现的一个业务取值。
    ADMIN = "admin"
    # 枚举说明：MEMBER 是该枚举允许出现的一个业务取值。
    MEMBER = "member"


# 类职责：FamilyMemberStatus 约束 家庭成员模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class FamilyMemberStatus(StrEnum):
    # 枚举说明：ACTIVE 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    ACTIVE = "active"
    # 枚举说明：LEFT 是该枚举允许出现的一个业务取值。
    LEFT = "left"
    # 枚举说明：REMOVED 是该枚举允许出现的一个业务取值。
    REMOVED = "removed"


# 类职责：FamilyInvitationStatus 约束 家庭成员模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class FamilyInvitationStatus(StrEnum):
    # 枚举说明：PENDING 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    PENDING = "pending"
    # 枚举说明：ACCEPTED 是该枚举允许出现的一个业务取值。
    ACCEPTED = "accepted"
    # 枚举说明：EXPIRED 是该枚举允许出现的一个业务取值。
    EXPIRED = "expired"
    # 枚举说明：CANCELLED 是该枚举允许出现的一个业务取值。
    CANCELLED = "cancelled"
