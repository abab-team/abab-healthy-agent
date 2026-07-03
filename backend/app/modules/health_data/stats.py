# 模块领域：健康指标模块
# 领域说明：负责血压、体重、睡眠、活动等可量化指标的录入、查询和统计。
# 文件职责：统计文件。对健康指标进行聚合、趋势和摘要计算。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from decimal import Decimal


# 函数职责：业务函数，封装 健康指标模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def data_quality_for_count(count: int) -> str:
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    if count >= 10:
        return "good"
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if count >= 3:
        return "partial"
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if count >= 1:
        return "insufficient"
    return "missing"


# 函数职责：业务函数，封装 健康指标模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def to_float(value: object) -> float | None:
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    if value is None:
        return None
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


# 函数职责：业务函数，封装 健康指标模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def average(values: list[float]) -> float | None:
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    if not values:
        return None
    return sum(values) / len(values)
