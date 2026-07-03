# 模块领域：健康报告模块
# 领域说明：负责日报、周报、家庭汇总和就医摘要的生成与渲染。
# 文件职责：枚举定义文件。集中约束状态、类型、来源等固定取值，避免魔法字符串散落在业务代码中。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from enum import StrEnum


# 类职责：DailyReportStatusLevel 约束 健康报告模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class DailyReportStatusLevel(StrEnum):
    # 枚举说明：NORMAL 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    NORMAL = "normal"
    # 枚举说明：ATTENTION 是该枚举允许出现的一个业务取值。
    ATTENTION = "attention"
    # 枚举说明：FOLLOW_UP 是该枚举允许出现的一个业务取值。
    FOLLOW_UP = "follow_up"
    # 枚举说明：INSUFFICIENT_DATA 是该枚举允许出现的一个业务取值。
    INSUFFICIENT_DATA = "insufficient_data"


# 类职责：DailyReportGeneratedBy 约束 健康报告模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class DailyReportGeneratedBy(StrEnum):
    # 枚举说明：SYSTEM 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    SYSTEM = "system"
    # 枚举说明：USER 是该枚举允许出现的一个业务取值。
    USER = "user"
    # 枚举说明：AGENT 是该枚举允许出现的一个业务取值。
    AGENT = "agent"


# 类职责：DailyReportGenerationStatus 约束 健康报告模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class DailyReportGenerationStatus(StrEnum):
    # 枚举说明：PENDING 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    PENDING = "pending"
    # 枚举说明：SUCCESS 是该枚举允许出现的一个业务取值。
    SUCCESS = "success"
    # 枚举说明：FAILED 是该枚举允许出现的一个业务取值。
    FAILED = "failed"
    # 枚举说明：SKIPPED 是该枚举允许出现的一个业务取值。
    SKIPPED = "skipped"
