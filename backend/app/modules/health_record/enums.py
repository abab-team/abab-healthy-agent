# 模块领域：健康记录模块
# 领域说明：负责症状、用药、就医、备注等事件型健康记录。
# 文件职责：枚举定义文件。集中约束状态、类型、来源等固定取值，避免魔法字符串散落在业务代码中。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from enum import StrEnum


# 类职责：SymptomRecordStatus 约束 健康记录模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class SymptomRecordStatus(StrEnum):
    # 枚举说明：ACTIVE 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    ACTIVE = "active"
    # 枚举说明：RESOLVED 是该枚举允许出现的一个业务取值。
    RESOLVED = "resolved"
    # 枚举说明：ARCHIVED 是该枚举允许出现的一个业务取值。
    ARCHIVED = "archived"


# 类职责：HealthRecordSource 约束 健康记录模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class HealthRecordSource(StrEnum):
    # 枚举说明：MANUAL 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    MANUAL = "manual"
    # 枚举说明：AI_EXTRACTED 是该枚举允许出现的一个业务取值。
    AI_EXTRACTED = "ai_extracted"
    # 枚举说明：IMPORTED 是该枚举允许出现的一个业务取值。
    IMPORTED = "imported"
    # 枚举说明：SYSTEM 是该枚举允许出现的一个业务取值。
    SYSTEM = "system"


# 类职责：HealthRecordDraftStatus 约束 健康记录模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class HealthRecordDraftStatus(StrEnum):
    # 枚举说明：PENDING 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    PENDING = "pending"
    # 枚举说明：CONFIRMED 是该枚举允许出现的一个业务取值。
    CONFIRMED = "confirmed"
    # 枚举说明：CANCELLED 是该枚举允许出现的一个业务取值。
    CANCELLED = "cancelled"
    # 枚举说明：EXPIRED 是该枚举允许出现的一个业务取值。
    EXPIRED = "expired"


# 类职责：HealthRecordDraftType 约束 健康记录模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class HealthRecordDraftType(StrEnum):
    # 枚举说明：SYMPTOM 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    SYMPTOM = "symptom"
    # 枚举说明：METRIC_CANDIDATE 是该枚举允许出现的一个业务取值。
    METRIC_CANDIDATE = "metric_candidate"
    # 枚举说明：MIXED_HEALTH_RECORD 是该枚举允许出现的一个业务取值。
    MIXED_HEALTH_RECORD = "mixed_health_record"
