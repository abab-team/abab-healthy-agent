# 模块领域：医疗时间线模块
# 领域说明：负责过敏、用药、手术、随访等长期医疗事件串联。
# 文件职责：枚举定义文件。集中约束状态、类型、来源等固定取值，避免魔法字符串散落在业务代码中。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from enum import StrEnum


# 类职责：MedicalEventType 约束 医疗时间线模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class MedicalEventType(StrEnum):
    # 枚举说明：CHECKUP 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    CHECKUP = "checkup"
    # 枚举说明：OUTPATIENT_VISIT 是该枚举允许出现的一个业务取值。
    OUTPATIENT_VISIT = "outpatient_visit"
    # 枚举说明：HOSPITALIZATION 是该枚举允许出现的一个业务取值。
    HOSPITALIZATION = "hospitalization"
    # 枚举说明：SURGERY 是该枚举允许出现的一个业务取值。
    SURGERY = "surgery"
    # 枚举说明：MEDICATION 是该枚举允许出现的一个业务取值。
    MEDICATION = "medication"
    # 枚举说明：ALLERGY 是该枚举允许出现的一个业务取值。
    ALLERGY = "allergy"
    # 枚举说明：CHRONIC_CONDITION 是该枚举允许出现的一个业务取值。
    CHRONIC_CONDITION = "chronic_condition"
    # 枚举说明：LAB_TEST 是该枚举允许出现的一个业务取值。
    LAB_TEST = "lab_test"
    # 枚举说明：DOCTOR_ADVICE 是该枚举允许出现的一个业务取值。
    DOCTOR_ADVICE = "doctor_advice"
    # 枚举说明：FOLLOW_UP 是该枚举允许出现的一个业务取值。
    FOLLOW_UP = "follow_up"
    # 枚举说明：OTHER 是该枚举允许出现的一个业务取值。
    OTHER = "other"


# 类职责：MedicalEventStatus 约束 医疗时间线模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class MedicalEventStatus(StrEnum):
    # 枚举说明：ACTIVE 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    ACTIVE = "active"
    # 枚举说明：ARCHIVED 是该枚举允许出现的一个业务取值。
    ARCHIVED = "archived"
    # 枚举说明：DELETED 是该枚举允许出现的一个业务取值。
    DELETED = "deleted"


# 类职责：MedicalEventSource 约束 医疗时间线模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class MedicalEventSource(StrEnum):
    # 枚举说明：MANUAL 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    MANUAL = "manual"
    # 枚举说明：DOCUMENT_EXTRACTED 是该枚举允许出现的一个业务取值。
    DOCUMENT_EXTRACTED = "document_extracted"
    # 枚举说明：IMPORTED 是该枚举允许出现的一个业务取值。
    IMPORTED = "imported"
    # 枚举说明：SYSTEM 是该枚举允许出现的一个业务取值。
    SYSTEM = "system"
