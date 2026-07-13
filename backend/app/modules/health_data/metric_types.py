# 模块领域：健康指标模块
# 领域说明：负责血压、体重、睡眠、活动等可量化指标的录入、查询和统计。
# 文件职责：业务代码文件。承载本模块的一部分领域能力或工程能力。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

"""Central metric presentation definitions used by services and Agent tools."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricDefinition:
    key: str
    label: str
    default_unit: str


METRIC_DEFINITIONS = {
    "sleep_duration": MetricDefinition("sleep_duration", "睡眠", "hours"),
    "steps": MetricDefinition("steps", "步数", "steps"),
    "weight": MetricDefinition("weight", "体重", "kg"),
    "heart_rate": MetricDefinition("heart_rate", "心率", "bpm"),
    "exercise_duration": MetricDefinition("exercise_duration", "运动时长", "minutes"),
    "body_fat": MetricDefinition("body_fat", "体脂", "%"),
    "temperature": MetricDefinition("temperature", "体温", "C"),
    "bmi": MetricDefinition("bmi", "BMI", "kg/m2"),
}


def get_metric_definition(metric_type: str) -> MetricDefinition | None:
    return METRIC_DEFINITIONS.get(str(metric_type))
