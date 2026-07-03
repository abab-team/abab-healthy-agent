# 模块领域：健康记录模块
# 领域说明：负责症状、用药、就医、备注等事件型健康记录。
# 文件职责：数据结构文件。定义服务层/API 的输入输出对象，隔离外部请求与内部 ORM 模型。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


# 类职责：SymptomSummary 是 健康记录模块 的数据传输结构，用于接口入参、出参或服务层结果。
# 设计边界：Schema 负责数据形状和校验，不直接访问数据库。
@dataclass(frozen=True)
class SymptomSummary:
    # 字段说明：days 是接口/服务层数据结构中的一个显式字段。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    days: int
    # 字段说明：count 是接口/服务层数据结构中的一个显式字段。
    count: int
    # 字段说明：active_count 是接口/服务层数据结构中的一个显式字段。
    active_count: int
    # 字段说明：follow_up_needed_count 是接口/服务层数据结构中的一个显式字段。
    follow_up_needed_count: int
    # 字段说明：latest_record 是接口/服务层数据结构中的一个显式字段。
    latest_record: dict | None
    # 字段说明：common_symptoms 是接口/服务层数据结构中的一个显式字段。
    common_symptoms: list[dict]
    # 字段说明：records 是接口/服务层数据结构中的一个显式字段。
    records: list[dict]
