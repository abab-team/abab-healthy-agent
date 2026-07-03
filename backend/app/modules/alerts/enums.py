# 模块领域：提醒模块
# 领域说明：负责提醒规则、提醒调度、状态流转和通知触发。
# 文件职责：枚举定义文件。集中约束状态、类型、来源等固定取值，避免魔法字符串散落在业务代码中。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from enum import StrEnum


# 类职责：AlertType 约束 提醒模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AlertType(StrEnum):
    # 枚举说明：METRIC_ATTENTION 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    METRIC_ATTENTION = "metric_attention"
    # 枚举说明：SYMPTOM_FOLLOW_UP 是该枚举允许出现的一个业务取值。
    SYMPTOM_FOLLOW_UP = "symptom_follow_up"
    # 枚举说明：MEDICAL_FOLLOW_UP 是该枚举允许出现的一个业务取值。
    MEDICAL_FOLLOW_UP = "medical_follow_up"
    # 枚举说明：MEDICATION_REMINDER 是该枚举允许出现的一个业务取值。
    MEDICATION_REMINDER = "medication_reminder"
    # 枚举说明：DATA_MISSING 是该枚举允许出现的一个业务取值。
    DATA_MISSING = "data_missing"
    # 枚举说明：DOCUMENT_REVIEW 是该枚举允许出现的一个业务取值。
    DOCUMENT_REVIEW = "document_review"


# 类职责：AlertLevel 约束 提醒模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AlertLevel(StrEnum):
    # 枚举说明：INFO 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    INFO = "info"
    # 枚举说明：ATTENTION 是该枚举允许出现的一个业务取值。
    ATTENTION = "attention"
    # 枚举说明：IMPORTANT 是该枚举允许出现的一个业务取值。
    IMPORTANT = "important"
    # 枚举说明：URGENT 是该枚举允许出现的一个业务取值。
    URGENT = "urgent"


# 类职责：AlertStatus 约束 提醒模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AlertStatus(StrEnum):
    # 枚举说明：ACTIVE 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    ACTIVE = "active"
    # 枚举说明：READ 是该枚举允许出现的一个业务取值。
    READ = "read"
    # 枚举说明：RESOLVED 是该枚举允许出现的一个业务取值。
    RESOLVED = "resolved"
    # 枚举说明：DISMISSED 是该枚举允许出现的一个业务取值。
    DISMISSED = "dismissed"
    # 枚举说明：EXPIRED 是该枚举允许出现的一个业务取值。
    EXPIRED = "expired"


# 类职责：AlertSource 约束 提醒模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AlertSource(StrEnum):
    # 枚举说明：RULE 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    RULE = "rule"
    # 枚举说明：AGENT 是该枚举允许出现的一个业务取值。
    AGENT = "agent"
    # 枚举说明：USER 是该枚举允许出现的一个业务取值。
    USER = "user"
    # 枚举说明：SYSTEM 是该枚举允许出现的一个业务取值。
    SYSTEM = "system"


# 类职责：AlertEventType 约束 提醒模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class AlertEventType(StrEnum):
    # 枚举说明：CREATED 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    CREATED = "created"
    # 枚举说明：READ 是该枚举允许出现的一个业务取值。
    READ = "read"
    # 枚举说明：RESOLVED 是该枚举允许出现的一个业务取值。
    RESOLVED = "resolved"
    # 枚举说明：DISMISSED 是该枚举允许出现的一个业务取值。
    DISMISSED = "dismissed"
    # 枚举说明：REOPENED 是该枚举允许出现的一个业务取值。
    REOPENED = "reopened"
    # 枚举说明：EXPIRED 是该枚举允许出现的一个业务取值。
    EXPIRED = "expired"
