# 模块领域：健康指标模块
# 领域说明：负责血压、体重、睡眠、活动等可量化指标的录入、查询和统计。
# 文件职责：数据结构文件。定义服务层/API 的输入输出对象，隔离外部请求与内部 ORM 模型。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


# 类职责：MetricSummary 是 健康指标模块 的数据传输结构，用于接口入参、出参或服务层结果。
# 设计边界：Schema 负责数据形状和校验，不直接访问数据库。
@dataclass(frozen=True)
class MetricSummary:
    # 字段说明：metric_type 是接口/服务层数据结构中的一个显式字段。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    metric_type: str
    # 字段说明：days 是接口/服务层数据结构中的一个显式字段。
    days: int
    # 字段说明：count 是接口/服务层数据结构中的一个显式字段。
    count: int
    # 字段说明：latest_value 是接口/服务层数据结构中的一个显式字段。
    latest_value: float | str | None
    # 字段说明：latest_measured_at 是接口/服务层数据结构中的一个显式字段。
    latest_measured_at: datetime | None
    # 字段说明：min_value 是接口/服务层数据结构中的一个显式字段。
    min_value: float | None
    # 字段说明：max_value 是接口/服务层数据结构中的一个显式字段。
    max_value: float | None
    # 字段说明：avg_value 是接口/服务层数据结构中的一个显式字段。
    avg_value: float | None
    # 字段说明：unit 是接口/服务层数据结构中的一个显式字段。
    unit: str | None
    # 字段说明：data_quality 是接口/服务层数据结构中的一个显式字段。
    data_quality: str
    # 字段说明：records 是接口/服务层数据结构中的一个显式字段。
    records: list[dict]


# 类职责：BloodPressureSummary 是 健康指标模块 的数据传输结构，用于接口入参、出参或服务层结果。
# 设计边界：Schema 负责数据形状和校验，不直接访问数据库。
@dataclass(frozen=True)
class BloodPressureSummary:
    # 字段说明：days 是接口/服务层数据结构中的一个显式字段。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    days: int
    # 字段说明：count 是接口/服务层数据结构中的一个显式字段。
    count: int
    # 字段说明：latest_systolic 是接口/服务层数据结构中的一个显式字段。
    latest_systolic: int | None
    # 字段说明：latest_diastolic 是接口/服务层数据结构中的一个显式字段。
    latest_diastolic: int | None
    # 字段说明：latest_pulse 是接口/服务层数据结构中的一个显式字段。
    latest_pulse: int | None
    # 字段说明：latest_measured_at 是接口/服务层数据结构中的一个显式字段。
    latest_measured_at: datetime | None
    # 字段说明：avg_systolic 是接口/服务层数据结构中的一个显式字段。
    avg_systolic: float | None
    # 字段说明：avg_diastolic 是接口/服务层数据结构中的一个显式字段。
    avg_diastolic: float | None
    # 字段说明：min_systolic 是接口/服务层数据结构中的一个显式字段。
    min_systolic: int | None
    # 字段说明：max_systolic 是接口/服务层数据结构中的一个显式字段。
    max_systolic: int | None
    # 字段说明：min_diastolic 是接口/服务层数据结构中的一个显式字段。
    min_diastolic: int | None
    # 字段说明：max_diastolic 是接口/服务层数据结构中的一个显式字段。
    max_diastolic: int | None
    # 字段说明：data_quality 是接口/服务层数据结构中的一个显式字段。
    data_quality: str
    # 字段说明：records 是接口/服务层数据结构中的一个显式字段。
    records: list[dict]
