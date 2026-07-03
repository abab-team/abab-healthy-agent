# 模块领域：健康指标模块
# 领域说明：负责血压、体重、睡眠、活动等可量化指标的录入、查询和统计。
# 文件职责：枚举定义文件。集中约束状态、类型、来源等固定取值，避免魔法字符串散落在业务代码中。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from enum import StrEnum


# 类职责：MetricType 约束 健康指标模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class MetricType(StrEnum):
    # 枚举说明：SLEEP_DURATION 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    SLEEP_DURATION = "sleep_duration"
    # 枚举说明：STEPS 是该枚举允许出现的一个业务取值。
    STEPS = "steps"
    # 枚举说明：WEIGHT 是该枚举允许出现的一个业务取值。
    WEIGHT = "weight"
    # 枚举说明：BMI 是该枚举允许出现的一个业务取值。
    BMI = "bmi"
    # 枚举说明：BODY_FAT 是该枚举允许出现的一个业务取值。
    BODY_FAT = "body_fat"
    # 枚举说明：HEART_RATE 是该枚举允许出现的一个业务取值。
    HEART_RATE = "heart_rate"
    # 枚举说明：BLOOD_OXYGEN 是该枚举允许出现的一个业务取值。
    BLOOD_OXYGEN = "blood_oxygen"
    # 枚举说明：TEMPERATURE 是该枚举允许出现的一个业务取值。
    TEMPERATURE = "temperature"
    # 枚举说明：BLOOD_GLUCOSE 是该枚举允许出现的一个业务取值。
    BLOOD_GLUCOSE = "blood_glucose"
    # 枚举说明：EXERCISE_DURATION 是该枚举允许出现的一个业务取值。
    EXERCISE_DURATION = "exercise_duration"


# 类职责：MetricSource 约束 健康指标模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class MetricSource(StrEnum):
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
    # 枚举说明：DEVICE 是该枚举允许出现的一个业务取值。
    DEVICE = "device"
    # 枚举说明：SYSTEM 是该枚举允许出现的一个业务取值。
    SYSTEM = "system"
    # 枚举说明：UNKNOWN 是该枚举允许出现的一个业务取值。
    UNKNOWN = "unknown"


# 类职责：ConfidenceLevel 约束 健康指标模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class ConfidenceLevel(StrEnum):
    # 枚举说明：HIGH 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    HIGH = "high"
    # 枚举说明：MEDIUM 是该枚举允许出现的一个业务取值。
    MEDIUM = "medium"
    # 枚举说明：LOW 是该枚举允许出现的一个业务取值。
    LOW = "low"
    # 枚举说明：UNKNOWN 是该枚举允许出现的一个业务取值。
    UNKNOWN = "unknown"


# 类职责：BloodPressureMeasurementContext 约束 健康指标模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class BloodPressureMeasurementContext(StrEnum):
    # 枚举说明：MORNING 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    MORNING = "morning"
    # 枚举说明：EVENING 是该枚举允许出现的一个业务取值。
    EVENING = "evening"
    # 枚举说明：BEFORE_MEDICATION 是该枚举允许出现的一个业务取值。
    BEFORE_MEDICATION = "before_medication"
    # 枚举说明：AFTER_MEDICATION 是该枚举允许出现的一个业务取值。
    AFTER_MEDICATION = "after_medication"
    # 枚举说明：AFTER_EXERCISE 是该枚举允许出现的一个业务取值。
    AFTER_EXERCISE = "after_exercise"
    # 枚举说明：UNKNOWN 是该枚举允许出现的一个业务取值。
    UNKNOWN = "unknown"


# 类职责：BloodPressureArm 约束 健康指标模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class BloodPressureArm(StrEnum):
    # 枚举说明：LEFT 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    LEFT = "left"
    # 枚举说明：RIGHT 是该枚举允许出现的一个业务取值。
    RIGHT = "right"
    # 枚举说明：UNKNOWN 是该枚举允许出现的一个业务取值。
    UNKNOWN = "unknown"


# 类职责：BloodPressurePosture 约束 健康指标模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class BloodPressurePosture(StrEnum):
    # 枚举说明：SITTING 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    SITTING = "sitting"
    # 枚举说明：STANDING 是该枚举允许出现的一个业务取值。
    STANDING = "standing"
    # 枚举说明：LYING 是该枚举允许出现的一个业务取值。
    LYING = "lying"
    # 枚举说明：UNKNOWN 是该枚举允许出现的一个业务取值。
    UNKNOWN = "unknown"


# 类职责：HealthDataImportType 约束 健康指标模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class HealthDataImportType(StrEnum):
    # 枚举说明：MANUAL_BATCH 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    MANUAL_BATCH = "manual_batch"
    # 枚举说明：CSV 是该枚举允许出现的一个业务取值。
    CSV = "csv"
    # 枚举说明：EXCEL 是该枚举允许出现的一个业务取值。
    EXCEL = "excel"
    # 枚举说明：DEVICE 是该枚举允许出现的一个业务取值。
    DEVICE = "device"
    # 枚举说明：SYSTEM 是该枚举允许出现的一个业务取值。
    SYSTEM = "system"


# 类职责：HealthDataImportStatus 约束 健康指标模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class HealthDataImportStatus(StrEnum):
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
    # 枚举说明：PARTIAL_SUCCESS 是该枚举允许出现的一个业务取值。
    PARTIAL_SUCCESS = "partial_success"
    # 枚举说明：CANCELLED 是该枚举允许出现的一个业务取值。
    CANCELLED = "cancelled"
