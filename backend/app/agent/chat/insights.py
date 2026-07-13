from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agent.chat.schemas import HealthQueryIntent, HealthQueryPlan
from app.agent.schemas import ToolExecutionResult


METRIC_LABELS = {
    "sleep_duration": "睡眠",
    "steps": "步数",
    "weight": "体重",
    "heart_rate": "心率",
    "exercise_duration": "运动时长",
}


@dataclass(frozen=True)
class HealthInsight:
    opening: str
    facts: tuple[str, ...]
    observations: tuple[str, ...]
    next_step: str

    def safe_facts(self) -> str:
        return "\n".join((*self.facts, *self.observations))[:1600]

    def render(self) -> str:
        sections = [self.opening]
        if self.facts:
            sections.append("\n".join(f"- {fact}" for fact in self.facts))
        if self.observations:
            sections.append("\n".join(f"- {item}" for item in self.observations))
        sections.append(self.next_step)
        sections.append("以上根据系统内记录整理，不替代医生判断。")
        return "\n".join(sections)


def build_health_insight(plan: HealthQueryPlan, results: list[ToolExecutionResult]) -> HealthInsight:
    member = plan.member_label or "你"
    period = _period_label(plan.time_range.days)
    topic = _topic_label(plan)
    opening = f"我帮你看了一下{member}{period}的{topic}记录。"
    if any(result.blocked or result.status != "completed" for result in results):
        return HealthInsight(
            opening=opening,
            facts=("部分信息因权限设置暂不可用。",),
            observations=(),
            next_step="如果需要，我可以继续整理当前可查看的其他记录。",
        )

    facts: list[str] = []
    observations: list[str] = []
    for result in results:
        _append_result_insight(plan, result.output_data or {}, facts, observations)
    if not facts:
        facts.append("系统内暂无相关记录；这不代表现实中没有相关情况。")
    if not observations and facts and not facts[0].startswith("系统内暂无"):
        observations.append("这些内容来自已保存的记录，适合继续积累后再观察变化。")
    return HealthInsight(
        opening=opening,
        facts=tuple(facts[:5]),
        observations=tuple(observations[:2]),
        next_step="如果你愿意，我也可以继续帮你整理最近一个月的记录，或准备就医沟通资料。",
    )


def _append_result_insight(
    plan: HealthQueryPlan,
    data: dict[str, Any],
    facts: list[str],
    observations: list[str],
) -> None:
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    count = _count(data, summary)
    if count <= 0:
        facts.append("系统内暂无相关记录；这不代表现实中没有相关情况。")
        return
    if plan.intent == HealthQueryIntent.QUERY_BLOOD_PRESSURE:
        facts.append(f"这段时间共记录 {count} 次血压。")
        systolic, diastolic = summary.get("latest_systolic"), summary.get("latest_diastolic")
        if systolic is not None and diastolic is not None:
            facts.append(f"最近一次已记录数值是 {systolic}/{diastolic} mmHg。")
        observations.append("我只整理已记录的数值，不对数值作医学判断。")
        return
    if plan.intent == HealthQueryIntent.QUERY_METRICS:
        metric = METRIC_LABELS.get(str(summary.get("metric_type") or plan.metric_type or ""), "这项指标")
        facts.append(f"这段时间共记录 {count} 条{metric}数据。")
        value = summary.get("avg_value") if plan.aggregation == "avg" else summary.get("latest_value")
        unit = summary.get("unit") or ""
        if value is not None:
            label = "平均已记录值" if plan.aggregation == "avg" else "最近一次已记录值"
            facts.append(f"{label}是 {value} {_unit_label(unit)}".strip())
        observations.append("记录较连续时，更容易回看长期变化。")
        return
    if plan.intent == HealthQueryIntent.QUERY_SYMPTOMS:
        facts.append(f"这段时间共保存 {count} 条症状记录。")
        observations.append("我只整理已保存的描述，不推断原因。")
        return
    if plan.intent == HealthQueryIntent.QUERY_DOCUMENTS:
        facts.append(f"系统内找到 {count} 份文档资料。")
        observations.append("资料标题和归档状态可在档案页继续查看；不会展示文件路径或原始全文。")
        return
    if plan.intent == HealthQueryIntent.QUERY_ALERTS:
        active = data.get("active_count")
        facts.append(f"这段时间共有 {count} 条提醒记录。")
        if active is not None:
            facts.append(f"其中当前仍在使用的提醒有 {active} 条。")
        observations.append("提醒用于日常安排，不是急救服务。")
        return
    if plan.intent == HealthQueryIntent.QUERY_MEDICAL_EVENTS:
        facts.append(f"这段时间共有 {count} 条健康事件记录。")
        return
    facts.append(f"系统内找到 {count} 条相关记录。")


def _count(data: dict[str, Any], summary: dict[str, Any]) -> int:
    value = data.get("count", summary.get("count", 0))
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _period_label(days: int) -> str:
    if days == 7:
        return "最近一周"
    if days == 30:
        return "最近一个月"
    if days == 1:
        return "今天"
    return f"最近 {days} 天"


def _topic_label(plan: HealthQueryPlan) -> str:
    if plan.intent == HealthQueryIntent.QUERY_DAILY_STATUS:
        return "健康记录"
    if plan.intent == HealthQueryIntent.QUERY_BLOOD_PRESSURE:
        return "血压"
    if plan.intent == HealthQueryIntent.QUERY_METRICS:
        return METRIC_LABELS.get(plan.metric_type or "", "健康指标")
    return {
        HealthQueryIntent.QUERY_SYMPTOMS: "症状",
        HealthQueryIntent.QUERY_MEDICAL_EVENTS: "健康事件",
        HealthQueryIntent.QUERY_DOCUMENTS: "资料",
        HealthQueryIntent.QUERY_ALERTS: "提醒",
    }.get(plan.intent, "健康")


def _unit_label(value: Any) -> str:
    return {"hours": "小时", "steps": "步", "kg": "kg", "bpm": "次/分"}.get(str(value or ""), str(value or ""))
