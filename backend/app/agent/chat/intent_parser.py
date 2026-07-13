from __future__ import annotations

from datetime import date

from app.agent.chat.member_resolver import resolve_member_label
from app.agent.chat.schemas import HealthQueryIntent, HealthQueryPlan
from app.agent.chat.time_range_parser import parse_time_range


METRIC_KEYWORDS = {
    "sleep_duration": ("睡眠", "睡觉", "睡了", "sleep"),
    "steps": ("步数", "走了", "走路", "steps"),
    "weight": ("体重", "weight"),
    "heart_rate": ("心率", "heart rate"),
    "bmi": ("bmi",),
    "exercise_duration": ("运动", "锻炼", "exercise"),
}


# Narrow overview phrases: these explicitly ask for the current user's
# recorded information and should execute the existing controlled overview.
SELF_OVERVIEW_PHRASES = (
    "\u67e5\u8be2\u6211\u6700\u8fd1\u7684\u6570\u636e",
    "\u67e5\u770b\u6211\u6700\u8fd1\u7684\u6570\u636e",
    "\u6211\u6700\u8fd1\u7684\u6570\u636e",
    "\u6211\u7684\u6700\u8fd1\u6570\u636e",
    "\u67e5\u8be2\u6211\u7684\u5065\u5eb7\u8bb0\u5f55",
    "\u67e5\u770b\u6211\u7684\u5065\u5eb7\u8bb0\u5f55",
    "\u6211\u6700\u8fd1\u600e\u4e48\u6837",
)


def parse_health_query(message: str, *, reference_date: date | None = None) -> HealthQueryPlan:
    text = (message or "").lower()
    time_range = parse_time_range(message, reference_date=reference_date)
    member_label, member_scope = resolve_member_label(message)
    aggregation = _aggregation_for(text)

    if any(phrase in text for phrase in SELF_OVERVIEW_PHRASES):
        return HealthQueryPlan(
            intent=HealthQueryIntent.QUERY_DAILY_STATUS,
            time_range=time_range,
            member_label=member_label,
            member_scope=member_scope,
            source_type="daily_status",
            tool_name="health_data.metrics.recent",
            tool_input={"days": time_range.days, "limit": 10},
        )

    if any(keyword in text for keyword in ("血压", "blood pressure")):
        return HealthQueryPlan(
            intent=HealthQueryIntent.QUERY_BLOOD_PRESSURE,
            time_range=time_range,
            member_label=member_label,
            member_scope=member_scope,
            metric_type="blood_pressure",
            aggregation=aggregation,
            tool_name="health_data.blood_pressure.summary",
            tool_input={"days": time_range.days},
        )
    for metric_type, keywords in METRIC_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return HealthQueryPlan(
                intent=HealthQueryIntent.QUERY_METRICS,
                time_range=time_range,
                member_label=member_label,
                member_scope=member_scope,
                metric_type=metric_type,
                aggregation=aggregation,
                tool_name="health_data.metric.summary",
                tool_input={"days": time_range.days, "metric_type": metric_type, "aggregation": aggregation},
            )
    if any(keyword in text for keyword in ("症状", "疼", "痛", "不舒服", "symptom")):
        return HealthQueryPlan(
            intent=HealthQueryIntent.QUERY_SYMPTOMS,
            time_range=time_range,
            member_label=member_label,
            member_scope=member_scope,
            source_type="symptoms",
            aggregation=aggregation,
            tool_name="health_record.symptoms.query",
            tool_input={"days": time_range.days},
        )
    if any(keyword in text for keyword in ("病史", "过敏", "用药记录", "手术", "住院", "复查是什么时候", "就医资料")):
        return HealthQueryPlan(
            intent=HealthQueryIntent.QUERY_MEDICAL_HISTORY,
            time_range=time_range,
            member_label=member_label,
            member_scope=member_scope,
            source_type="medical_history",
            tool_name="health_profile.get",
            tool_input={"days": time_range.days},
        )
    if any(keyword in text for keyword in ("复查", "随访", "就诊", "检查记录", "健康事件", "medical event", "follow-up")):
        intent = HealthQueryIntent.QUERY_ALERTS if any(k in text for k in ("提醒", "reminder")) else HealthQueryIntent.QUERY_MEDICAL_EVENTS
        return HealthQueryPlan(
            intent=intent,
            time_range=time_range,
            member_label=member_label,
            member_scope=member_scope,
            source_type="alerts" if intent == HealthQueryIntent.QUERY_ALERTS else "medical_events",
            aggregation=aggregation,
            tool_name="alerts.query" if intent == HealthQueryIntent.QUERY_ALERTS else "medical_timeline.events.query",
            tool_input={"days": time_range.days, "limit": 10},
        )
    if any(keyword in text for keyword in ("资料", "文档", "上传", "报告", "document", "file")):
        return HealthQueryPlan(
            intent=HealthQueryIntent.QUERY_DOCUMENTS,
            time_range=time_range,
            member_label=member_label,
            member_scope=member_scope,
            source_type="documents",
            tool_name="documents.query",
            tool_input={"limit": 10},
        )
    if any(keyword in text for keyword in ("提醒", "待办", "alert", "reminder")):
        return HealthQueryPlan(
            intent=HealthQueryIntent.QUERY_ALERTS,
            time_range=time_range,
            member_label=member_label,
            member_scope=member_scope,
            source_type="alerts",
            tool_name="alerts.query",
            tool_input={"days": time_range.days, "limit": 10},
        )
    if member_scope == "family" and any(keyword in text for keyword in ("怎么样", "近况", "身体情况", "健康情况")):
        return HealthQueryPlan(
            intent=HealthQueryIntent.QUERY_DAILY_STATUS,
            time_range=time_range,
            member_label=member_label,
            member_scope=member_scope,
            source_type="daily_status",
            tool_name="health_data.metrics.recent",
            tool_input={"days": time_range.days, "limit": 10},
        )
    if any(keyword in text for keyword in ("健康情况", "健康状态", "总结", "概览", "今天怎么样", "status", "summary")):
        return HealthQueryPlan(
            intent=HealthQueryIntent.QUERY_DAILY_STATUS,
            time_range=time_range,
            member_label=member_label,
            member_scope=member_scope,
            source_type="daily_status",
            tool_name="health_data.metrics.recent",
            tool_input={"days": time_range.days, "limit": 10},
        )
    return HealthQueryPlan(
        intent=HealthQueryIntent.UNKNOWN,
        time_range=time_range,
        member_label=member_label,
        member_scope=member_scope,
        safe_unknown_reason="unsupported_health_query_intent",
    )


def _aggregation_for(text: str) -> str:
    if any(keyword in text for keyword in ("平均", "均值", "average", "avg")):
        return "avg"
    if any(keyword in text for keyword in ("多少次", "几次", "次数", "count")):
        return "count"
    if any(keyword in text for keyword in ("最近一次", "最新", "latest")):
        return "latest"
    if any(keyword in text for keyword in ("总共", "合计", "sum")):
        return "sum"
    return "summary"
