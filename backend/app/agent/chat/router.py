from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.agent.chat.schemas import HealthQueryPlan


class ConversationIntent(StrEnum):
    CASUAL_CHAT = "casual_chat"
    HEALTH_RECORD_QUERY = "health_record_query"
    FAMILY_HEALTH_QUERY = "family_health_query"
    HEALTH_KNOWLEDGE = "health_knowledge"
    DOCUMENT_TASK = "document_task"
    RECORD_TASK = "record_task"
    # Backward-compatible alias for callers from the previous chat workflow.
    WRITE_REQUEST = "record_task"
    OTHER = "other"


class SuggestedAction(StrEnum):
    SYMPTOM_DRAFT = "symptom_draft"
    HEALTH_EVENT_DRAFT = "health_event_draft"
    HEALTH_ALERT = "health_alert"


@dataclass(frozen=True)
class ConversationRoute:
    intent: ConversationIntent
    suggested_action: SuggestedAction | None = None


_WRITE_SYMPTOM_TERMS = ("头晕", "头痛", "不舒服", "症状", "睡不好", "咳嗽", "发烧")
_WRITE_REQUEST_MARKERS = ("帮我记录", "记录一下", "记一下", "记录今天", "帮我记")
_WRITE_EVENT_TERMS = ("就医记录", "检查记录", "复查记录", "健康事件", "门诊记录")
_WRITE_ALERT_TERMS = ("提醒我", "创建提醒", "设个提醒", "健康提醒")
_WRITE_EVENT_RECORD_TERMS = ("体温", "温度", "血压", "睡眠", "体重", "步数")
_WRITE_CONTINUATION_MARKERS = ("整理", "继续", "刚才那个", "刚才的")
_DOCUMENT_TASK_MARKERS = ("整理体检资料", "整理检查资料", "整理医疗资料", "就医资料摘要", "就医摘要")
_HEALTH_KNOWLEDGE_TERMS = (
    "为什么会",
    "什么原因",
    "是什么原因",
    "怎么改善",
    "如何改善",
    "怎么缓解",
    "什么是",
    "睡不好",
    "睡眠不好",
    "感冒",
    "发烧",
    "咳嗽",
)
_HEALTH_RECORD_HINTS = (
    "血压", "睡眠", "步数", "体重", "心率", "症状", "提醒", "文档", "报告", "复查",
    "pressure", "sleep", "steps", "weight", "symptom", "alert", "document", "report",
)
_HEALTH_INTERPRETATION_TERMS = (
    "\u8fd9\u4e2a\u6570\u503c\u5065\u5eb7\u5417",
    "\u8fd9\u4e2a\u6570\u636e\u5065\u5eb7\u5417",
    "\u6b63\u5e38\u5417",
    "\u5f02\u5e38\u5417",
    "\u6709\u95ee\u9898\u5417",
    "\u4e25\u91cd\u5417",
    "\u6211\u5065\u5eb7\u5417",
)
_EXTERNAL_REALTIME_TERMS = ("天气", "weather", "新闻", "news", "股价", "股票", "汇率")
_CASUAL_CHAT_TERMS = ("你好", "您好", "早上好", "晚上好", "今天怎么样", "今天过得怎么样", "谢谢", "感谢", "再见")


def route_conversation(
    message: str,
    plan: HealthQueryPlan,
    *,
    pending_action: SuggestedAction | str | None = None,
) -> ConversationRoute:
    """Route by deterministic rules; models never select a tool or target user."""
    text = (message or "").strip().lower()
    if text in _CASUAL_CHAT_TERMS:
        return ConversationRoute(ConversationIntent.CASUAL_CHAT)
    if pending_action and any(marker in text for marker in _WRITE_CONTINUATION_MARKERS):
        try:
            return ConversationRoute(ConversationIntent.RECORD_TASK, SuggestedAction(pending_action))
        except ValueError:
            pass
    if any(term in text for term in _DOCUMENT_TASK_MARKERS):
        return ConversationRoute(ConversationIntent.DOCUMENT_TASK)
    if any(term in text for term in _WRITE_ALERT_TERMS):
        return ConversationRoute(ConversationIntent.RECORD_TASK, SuggestedAction.HEALTH_ALERT)
    if any(term in text for term in _WRITE_EVENT_TERMS):
        return ConversationRoute(ConversationIntent.RECORD_TASK, SuggestedAction.HEALTH_EVENT_DRAFT)
    if text.startswith("记录") and any(term in text for term in _WRITE_EVENT_RECORD_TERMS):
        return ConversationRoute(ConversationIntent.RECORD_TASK, SuggestedAction.HEALTH_EVENT_DRAFT)
    if any(marker in text for marker in _WRITE_REQUEST_MARKERS) and any(term in text for term in _WRITE_SYMPTOM_TERMS):
        return ConversationRoute(ConversationIntent.RECORD_TASK, SuggestedAction.SYMPTOM_DRAFT)
    if any(marker in text for marker in _WRITE_REQUEST_MARKERS) and any(term in text for term in _WRITE_EVENT_RECORD_TERMS):
        return ConversationRoute(ConversationIntent.RECORD_TASK, SuggestedAction.HEALTH_EVENT_DRAFT)
    if any(term in text for term in _HEALTH_INTERPRETATION_TERMS) and (plan.is_unknown or not plan.tool_name):
        return ConversationRoute(ConversationIntent.HEALTH_KNOWLEDGE)
    if any(term in text for term in _HEALTH_KNOWLEDGE_TERMS):
        return ConversationRoute(ConversationIntent.HEALTH_KNOWLEDGE)
    if any(term in text for term in _EXTERNAL_REALTIME_TERMS):
        return ConversationRoute(ConversationIntent.OTHER)
    if not plan.is_unknown and plan.tool_name:
        return ConversationRoute(
            ConversationIntent.FAMILY_HEALTH_QUERY if plan.member_scope == "family" else ConversationIntent.HEALTH_RECORD_QUERY
        )
    if any(term in text for term in _HEALTH_RECORD_HINTS):
        return ConversationRoute(ConversationIntent.HEALTH_RECORD_QUERY)
    return ConversationRoute(ConversationIntent.CASUAL_CHAT if text else ConversationIntent.OTHER)
