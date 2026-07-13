from __future__ import annotations

from dataclasses import dataclass
import re
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
        sections.extend((self.next_step, "以上根据系统内记录整理，不替代医生判断。"))
        return "\n".join(sections)


@dataclass(frozen=True)
class HealthOverview:
    """A safe aggregate assembled from ToolExecutor results, never from a DB."""

    available_sections: tuple[str, ...]
    unavailable_sections: tuple[str, ...]
    facts: tuple[str, ...]


def explain_blood_pressure_reference(user_message: str) -> str | None:
    """Explain an explicitly supplied blood-pressure value without diagnosing.

    This helper deliberately works only from the number the user typed. It
    neither reads health data nor infers a diagnosis, and gives the responder a
    concise, consistent explanation when a person asks about a single reading.
    """
    match = re.search(r"(?<!\d)(\d{2,3})\s*/\s*(\d{2,3})(?:\s*mmhg)?", user_message.lower())
    if not match:
        return None

    systolic, diastolic = (int(match.group(1)), int(match.group(2)))
    reference = "\u5e38\u89c1\u6210\u4eba\u9759\u606f\u8840\u538b\u53c2\u8003\u533a\u95f4\uff08\u6536\u7f29\u538b\u4f4e\u4e8e 120\u3001\u8212\u5f20\u538b\u4f4e\u4e8e 80 mmHg\uff09"
    if systolic < 120 and diastolic < 80:
        range_note = "\u843d\u5728" + reference + "\u5185"
    elif systolic >= 130 or diastolic >= 80:
        range_note = "\u5176\u4e2d\u4e00\u9879\u9ad8\u4e8e" + reference
    else:
        range_note = "\u4e0e" + reference + "\u7684\u8fb9\u754c\u63a5\u8fd1"

    return (
        f"\u4f60\u63d0\u5230\u7684 {systolic}/{diastolic} mmHg\uff0c\u4ece\u8fd9\u4e00\u6b21\u8bb0\u5f55\u770b\uff0c{range_note}\u3002"
        "\u5355\u6b21\u6d4b\u91cf\u4e0d\u80fd\u4ee3\u8868\u6574\u4f53\u5065\u5eb7\u60c5\u51b5\uff0c\u6211\u53ef\u4ee5\u7ee7\u7eed\u5e2e\u4f60\u67e5\u770b\u6700\u8fd1 7 \u5929\u6216 30 \u5929\u7684\u8d8b\u52bf\u3001\u8bb0\u5f55\u6b21\u6570\u548c\u53d8\u5316\u3002"
    )


def build_health_insight(plan: HealthQueryPlan, results: list[ToolExecutionResult]) -> HealthInsight:
    if plan.intent == HealthQueryIntent.QUERY_DAILY_STATUS:
        return _build_overview_insight(plan, results)

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
        observations.append("这些内容来自已保存的记录，后续持续记录会更方便回看变化。")
    return HealthInsight(
        opening=opening,
        facts=tuple(facts[:5]),
        observations=tuple(observations[:2]),
        next_step="如果你愿意，我也可以继续帮你整理最近一个月的记录，或准备就医沟通资料。",
    )


def _build_overview_insight(plan: HealthQueryPlan, results: list[ToolExecutionResult]) -> HealthInsight:
    """Turn the controlled overview into family-friendly, non-medical wording."""
    member = plan.member_label or "你"
    overview = _build_health_overview(results)
    facts = list(overview.facts)
    if overview.unavailable_sections:
        facts.append("部分信息因权限设置暂不可用。")
    if not facts:
        facts.append("系统内暂无这段时间的相关记录；这不代表现实中没有相关情况。")

    if len(overview.available_sections) >= 2:
        observations = ("系统内已有多个类别的记录，可以按时间范围继续回看变化。",)
    elif overview.available_sections:
        observations = ("当前可查看的资料覆盖范围有限，后续持续记录会更方便整理。",)
    else:
        observations = ()

    next_step = "如果需要，我也可以继续整理最近一个月的变化，或汇总已有资料供就医沟通时参考。"
    return HealthInsight(
        opening=f"我整理了一下{member}{_period_label(plan.time_range.days)}的健康情况。",
        facts=tuple(facts[:8]),
        observations=observations,
        next_step=next_step,
    )


def _build_health_overview(results: list[ToolExecutionResult]) -> HealthOverview:
    available: list[str] = []
    unavailable: list[str] = []
    facts: list[str] = []
    for result in results:
        label = _overview_label(result.tool_name)
        if result.blocked or result.status != "completed":
            unavailable.append(label)
            continue
        data = result.output_data or {}
        summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
        count = _count(data, summary)
        if result.tool_name == "health_data.metrics.recent":
            facts.append(
                f"健康指标：已记录 {count} 条数据。" if count else "健康指标：系统内暂无相关记录。"
            )
        elif result.tool_name == "health_data.blood_pressure.summary":
            systolic, diastolic = summary.get("latest_systolic"), summary.get("latest_diastolic")
            if count and systolic is not None and diastolic is not None:
                facts.append(f"血压记录：共 {count} 次，最近一次为 {systolic}/{diastolic} mmHg。")
            elif count:
                facts.append(f"血压记录：共 {count} 次。")
            else:
                facts.append("血压记录：系统内暂无相关记录。")
        elif result.tool_name == "health_record.symptoms.query":
            facts.append(f"症状记录：已保存 {count} 条。" if count else "症状记录：系统内暂无相关记录。")
        elif result.tool_name == "documents.query":
            facts.append(f"文档资料：已保存 {count} 份。" if count else "文档资料：系统内暂无相关记录。")
        elif result.tool_name == "medical_timeline.events.query":
            if count:
                follow_up = int(data.get("follow_up_needed_count") or 0)
                suffix = f"，其中标注待随访 {follow_up} 条" if follow_up else ""
                facts.append(f"健康事件：已记录 {count} 条{suffix}。")
            else:
                facts.append("健康事件：系统内暂无相关记录。")
        elif result.tool_name == "alerts.query":
            active = data.get("active_count")
            if count:
                suffix = f"，当前可用 {active} 条" if active is not None else ""
                facts.append(f"日常提醒：已保存 {count} 条{suffix}。")
            else:
                facts.append("日常提醒：系统内暂无相关记录。")
        available.append(label)
    return HealthOverview(tuple(available), tuple(unavailable), tuple(facts))


def _overview_label(tool_name: str) -> str:
    return {
        "health_data.metrics.recent": "健康指标",
        "health_data.blood_pressure.summary": "血压记录",
        "health_record.symptoms.query": "症状记录",
        "documents.query": "文档资料",
        "medical_timeline.events.query": "健康事件",
        "alerts.query": "日常提醒",
    }.get(tool_name, "健康资料")


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
        return "健康情况"
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
