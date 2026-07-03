# 模块领域：用户身份模块
# 领域说明：负责用户账号、登录会话、认证令牌和第三方身份关联。
# 文件职责：枚举定义文件。集中约束状态、类型、来源等固定取值，避免魔法字符串散落在业务代码中。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from enum import StrEnum


# 类职责：UserStatus 约束 用户身份模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class UserStatus(StrEnum):
    # 枚举说明：ACTIVE 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    ACTIVE = "active"
    # 枚举说明：DISABLED 是该枚举允许出现的一个业务取值。
    DISABLED = "disabled"
    # 枚举说明：DELETED 是该枚举允许出现的一个业务取值。
    DELETED = "deleted"


# 类职责：Gender 约束 用户身份模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class Gender(StrEnum):
    # 枚举说明：MALE 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    MALE = "male"
    # 枚举说明：FEMALE 是该枚举允许出现的一个业务取值。
    FEMALE = "female"
    # 枚举说明：OTHER 是该枚举允许出现的一个业务取值。
    OTHER = "other"
    # 枚举说明：UNKNOWN 是该枚举允许出现的一个业务取值。
    UNKNOWN = "unknown"


# 类职责：AuthProvider 约束 用户身份模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AuthProvider(StrEnum):
    # 枚举说明：PHONE 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    PHONE = "phone"
    # 枚举说明：EMAIL 是该枚举允许出现的一个业务取值。
    EMAIL = "email"
    # 枚举说明：WECHAT 是该枚举允许出现的一个业务取值。
    WECHAT = "wechat"
    # 枚举说明：GOOGLE 是该枚举允许出现的一个业务取值。
    GOOGLE = "google"
    # 枚举说明：APPLE 是该枚举允许出现的一个业务取值。
    APPLE = "apple"
