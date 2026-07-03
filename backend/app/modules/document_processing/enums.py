# 模块领域：文档处理模块
# 领域说明：负责 OCR、信息抽取、人工确认和结构化入库流程。
# 文件职责：枚举定义文件。集中约束状态、类型、来源等固定取值，避免魔法字符串散落在业务代码中。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from enum import StrEnum


# 类职责：DocumentProcessingJobType 约束 文档处理模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class DocumentProcessingJobType(StrEnum):
    # 枚举说明：TEXT_READ 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    TEXT_READ = "text_read"
    # 枚举说明：OCR 是该枚举允许出现的一个业务取值。
    OCR = "ocr"
    # 枚举说明：AI_EXTRACT 是该枚举允许出现的一个业务取值。
    AI_EXTRACT = "ai_extract"
    # 枚举说明：EVENT_DRAFT_GENERATE 是该枚举允许出现的一个业务取值。
    EVENT_DRAFT_GENERATE = "event_draft_generate"


# 类职责：DocumentProcessingStatus 约束 文档处理模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class DocumentProcessingStatus(StrEnum):
    # 枚举说明：PENDING 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    PENDING = "pending"
    # 枚举说明：PROCESSING 是该枚举允许出现的一个业务取值。
    PROCESSING = "processing"
    # 枚举说明：SUCCESS 是该枚举允许出现的一个业务取值。
    SUCCESS = "success"
    # 枚举说明：FAILED 是该枚举允许出现的一个业务取值。
    FAILED = "failed"
    # 枚举说明：CANCELLED 是该枚举允许出现的一个业务取值。
    CANCELLED = "cancelled"


# 类职责：DocumentExtractionMode 约束 文档处理模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class DocumentExtractionMode(StrEnum):
    # 枚举说明：BASIC 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    BASIC = "basic"
    # 枚举说明：STANDARD 是该枚举允许出现的一个业务取值。
    STANDARD = "standard"
    # 枚举说明：DETAILED 是该枚举允许出现的一个业务取值。
    DETAILED = "detailed"


# 类职责：DocumentExtractionResultStatus 约束 文档处理模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class DocumentExtractionResultStatus(StrEnum):
    # 枚举说明：DRAFT 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    DRAFT = "draft"
    # 枚举说明：NEEDS_REVIEW 是该枚举允许出现的一个业务取值。
    NEEDS_REVIEW = "needs_review"
    # 枚举说明：CONFIRMED 是该枚举允许出现的一个业务取值。
    CONFIRMED = "confirmed"
    # 枚举说明：REJECTED 是该枚举允许出现的一个业务取值。
    REJECTED = "rejected"
    # 枚举说明：FAILED 是该枚举允许出现的一个业务取值。
    FAILED = "failed"


# 类职责：MedicalEventDraftStatus 约束 文档处理模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class MedicalEventDraftStatus(StrEnum):
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
