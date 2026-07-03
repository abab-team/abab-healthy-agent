# 模块领域：健康资料中心
# 领域说明：负责体检报告、化验单、处方等文件的元数据、权限和存储引用。
# 文件职责：枚举定义文件。集中约束状态、类型、来源等固定取值，避免魔法字符串散落在业务代码中。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from enum import StrEnum


# 类职责：DocumentType 约束 健康资料中心 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class DocumentType(StrEnum):
    # 枚举说明：CHECKUP_REPORT 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    CHECKUP_REPORT = "checkup_report"
    # 枚举说明：MEDICAL_RECORD 是该枚举允许出现的一个业务取值。
    MEDICAL_RECORD = "medical_record"
    # 枚举说明：LAB_TEST 是该枚举允许出现的一个业务取值。
    LAB_TEST = "lab_test"
    # 枚举说明：SURGERY_RECORD 是该枚举允许出现的一个业务取值。
    SURGERY_RECORD = "surgery_record"
    # 枚举说明：DISCHARGE_SUMMARY 是该枚举允许出现的一个业务取值。
    DISCHARGE_SUMMARY = "discharge_summary"
    # 枚举说明：PRESCRIPTION 是该枚举允许出现的一个业务取值。
    PRESCRIPTION = "prescription"
    # 枚举说明：DOCTOR_ADVICE 是该枚举允许出现的一个业务取值。
    DOCTOR_ADVICE = "doctor_advice"
    # 枚举说明：IMAGE_NOTE 是该枚举允许出现的一个业务取值。
    IMAGE_NOTE = "image_note"
    # 枚举说明：OTHER 是该枚举允许出现的一个业务取值。
    OTHER = "other"


# 类职责：DocumentExtractStatus 约束 健康资料中心 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class DocumentExtractStatus(StrEnum):
    # 枚举说明：NOT_STARTED 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    NOT_STARTED = "not_started"
    # 枚举说明：PROCESSING 是该枚举允许出现的一个业务取值。
    PROCESSING = "processing"
    # 枚举说明：SUCCESS 是该枚举允许出现的一个业务取值。
    SUCCESS = "success"
    # 枚举说明：FAILED 是该枚举允许出现的一个业务取值。
    FAILED = "failed"
    # 枚举说明：NEEDS_REVIEW 是该枚举允许出现的一个业务取值。
    NEEDS_REVIEW = "needs_review"
    # 枚举说明：CONFIRMED 是该枚举允许出现的一个业务取值。
    CONFIRMED = "confirmed"


# 类职责：DocumentVisibility 约束 健康资料中心 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class DocumentVisibility(StrEnum):
    # 枚举说明：PRIVATE 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    PRIVATE = "private"
    # 枚举说明：FAMILY_SHARED 是该枚举允许出现的一个业务取值。
    FAMILY_SHARED = "family_shared"


# 类职责：DocumentSource 约束 健康资料中心 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class DocumentSource(StrEnum):
    # 枚举说明：UPLOAD 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    UPLOAD = "upload"
    # 枚举说明：MANUAL 是该枚举允许出现的一个业务取值。
    MANUAL = "manual"
    # 枚举说明：IMPORTED 是该枚举允许出现的一个业务取值。
    IMPORTED = "imported"
    # 枚举说明：SYSTEM 是该枚举允许出现的一个业务取值。
    SYSTEM = "system"
