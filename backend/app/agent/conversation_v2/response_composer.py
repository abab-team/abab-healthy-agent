"""Natural-language response composition for controlled conversation facts.

This module deliberately sits after the server-owned router and ToolExecutor.
It receives only compact allowlisted tool summaries, never a database handle,
tool definitions, permissions, identifiers, file paths, or raw source text.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import time
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from app.agent.safety import AgentSafetyPolicy
from app.agent.persona import CONVERSATION_PERSONA_GUIDANCE
from app.core.config import Settings
from app.llm.client import LLMClient
from app.llm.schemas import LLMMessage


CONVERSATION_ASSURANCE_TERMS = (
    "可以放心",
    "尽管放心",
    "一定没事",
    "没有问题",
    "你很健康",
    "完全健康",
    "让人放心",
    "请放心",
    "没什么问题",
    "身体很好",
    "整体挺平稳",
    "整体很平稳",
)
CONVERSATION_MEDICAL_SENTENCE_TERMS = (
    "诊断界限",
    "诊断为",
    "确诊",
    "处方",
    "剂量",
    "停药",
    "换药",
    "加量",
    "减药",
    "你患有",
    "你得了",
)


def has_disallowed_assurance(content: str) -> bool:
    """Keep certainty claims out of conversational health output."""
    return any(term in str(content or "") for term in CONVERSATION_ASSURANCE_TERMS)


def remove_disallowed_assurance_sentences(content: str) -> str:
    """Remove a narrow certainty sentence while preserving grounded facts."""
    pieces = re.split(r"(?<=[。！？!?])", str(content or ""))
    return "".join(piece for piece in pieces if not has_disallowed_assurance(piece)).strip()


def remove_disallowed_medical_sentences(content: str) -> str:
    """Remove diagnostic or treatment sentences from an otherwise safe explanation."""
    normalized = str(content or "").replace("不能作为诊断依据", "不能代表长期情况")
    pieces = re.split(r"(?<=[。！？!?])", normalized)
    return "".join(
        piece
        for piece in pieces
        if not any(term in piece for term in CONVERSATION_MEDICAL_SENTENCE_TERMS)
    ).strip()


def safe_conversation_replacement() -> str:
    return "我可以基于已记录数据做整理和一般说明，但不能据此给出确定性的健康结论。"


COMPOSER_SYSTEM_PROMPT = """你是家庭健康管家，负责把已经核验过的健康记录事实说得自然、清楚、有人情味。

只使用消息中提供的“安全事实包”，不要补充、猜测或改写其中没有的医疗事实。你不能诊断疾病、下结论、给出处方、药物剂量、停药或治疗建议；也不能声称可以读取数据库、决定权限或修改记录。不要提及工具、Trace、提示词或系统内部实现。

健康记录回复先直接回答问题，再用简短自然的语言整理事实；如合适，再给一个与当前数据有关的下一步查看方向。语气温和、简洁，像长期陪伴的家庭健康助手，不像客服或数据报告。只有安全事实包要求时，才在结尾加一次“内容基于系统内已有记录整理，不替代医生判断。”普通聊天和连续健康追问不要重复这句。
"""
@dataclass(frozen=True)
class SafeConversationFacts:
    """A prompt-safe representation of one server-authorized health answer."""

    topic: str
    subject: str
    period: str
    facts: tuple[str, ...]
    unavailable: tuple[str, ...]
    next_actions: tuple[str, ...]
    boundary_required: bool

    def as_prompt_payload(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "subject": self.subject,
            "period": self.period,
            "facts": list(self.facts),
            "unavailable": list(self.unavailable),
            "next_actions": list(self.next_actions),
            "boundary_required": self.boundary_required,
        }


@dataclass(frozen=True)
class ComposerResult:
    content: str
    llm_used: bool
    fallback_used: bool
    fallback_reason: str | None = None


class ConversationResponseComposer:
    """Lets the LLM express safe facts while retaining deterministic fallback."""

    def __init__(self, *, settings: Settings, llm_client: LLMClient) -> None:
        self.settings = settings
        self.llm_client = llm_client
        self.safety = AgentSafetyPolicy()

    def compose(
        self,
        *,
        history: list[BaseMessage],
        user_question: str,
        facts: SafeConversationFacts,
        fallback_answer: str,
    ) -> ComposerResult:
        if not (self.settings.LLM_ENABLED and self.settings.LLM_CHAT_ENABLED):
            return ComposerResult(fallback_answer, llm_used=False, fallback_used=True, fallback_reason="llm_disabled")

        content = ""
        for attempt in range(2):
            try:
                response = self.llm_client.chat(
                    _composer_messages(history=history, user_question=user_question, facts=facts),
                    metadata={"conversation_runtime": "v2", "response_composer": "safe_facts"},
                )
                content = _clean_content(response.content)
                break
            except Exception:
                if attempt == 0:
                    # The Agent's tool-call and composition requests can arrive
                    # back-to-back; retry a transient provider throttle once.
                    time.sleep(0.8)
        if not content:
            return ComposerResult(fallback_answer, llm_used=False, fallback_used=True, fallback_reason="llm_error")

        if not content:
            return ComposerResult(fallback_answer, llm_used=True, fallback_used=True, fallback_reason="empty_output")
        content = remove_disallowed_medical_sentences(content)
        if not content:
            return ComposerResult(fallback_answer, llm_used=True, fallback_used=True, fallback_reason="output_safety_blocked")
        decision = self.safety.evaluate_output(content, workflow_type="chat_workflow")
        if decision.blocked:
            return ComposerResult(fallback_answer, llm_used=True, fallback_used=True, fallback_reason="output_safety_blocked")
        content = remove_disallowed_assurance_sentences(content)
        if not content:
            return ComposerResult(fallback_answer, llm_used=True, fallback_used=True, fallback_reason="assurance_only_output")
        if not _is_grounded(content, facts):
            return ComposerResult(fallback_answer, llm_used=True, fallback_used=True, fallback_reason="ungrounded_output")

        if facts.boundary_required and "不替代医生判断" not in content:
            content = f"{content}\n\n内容基于系统内已有记录整理，不替代医生判断。"
        return ComposerResult(content, llm_used=True, fallback_used=False)


def build_safe_conversation_facts(
    *,
    state: dict[str, Any],
    messages: list[BaseMessage],
) -> SafeConversationFacts:
    """Build a small fact package from ToolExecutor-safe result summaries only."""
    plan = state.get("plan_summary") if isinstance(state.get("plan_summary"), dict) else {}
    resolved = state.get("resolved_member_context") if isinstance(state.get("resolved_member_context"), dict) else {}
    results = state.get("tool_execution_results")
    if not isinstance(results, list) or not results:
        payload = _latest_tool_payload(messages)
        results = [payload] if payload else []

    business_payload = next((item for item in results if isinstance(item, dict) and item.get("capability")), None)
    if isinstance(business_payload, dict):
        return _facts_from_business_payload(business_payload, messages)

    subject = str(resolved.get("member") or plan.get("member_label") or "你")
    period = _period_label(plan)
    facts: list[str] = []
    unavailable: list[str] = []
    seen_tools: set[str] = set()
    for result in results:
        if not isinstance(result, dict):
            continue
        tool = str(result.get("tool") or "")
        if not tool or tool in seen_tools:
            continue
        seen_tools.add(tool)
        if result.get("blocked") or result.get("status") != "completed":
            unavailable.append("部分相关信息因权限设置或当前数据状态暂不可用")
            continue
        summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
        count = _as_number(result.get("count"))
        if result.get("empty") or not count:
            facts.append(_empty_fact_for_tool(tool, plan))
            continue
        facts.extend(_facts_for_tool(tool=tool, summary=summary, count=count, plan=plan))

    if not facts and not unavailable:
        facts.append("系统内暂无可用于本次整理的相关记录")
    topic = _topic_label(str(plan.get("intent") or ""), results)
    return SafeConversationFacts(
        topic=topic,
        subject=subject,
        period=period,
        facts=tuple(facts[:8]),
        unavailable=tuple(dict.fromkeys(unavailable)),
        next_actions=_next_actions(topic),
        boundary_required=not _has_recent_health_boundary(messages),
    )


def _facts_from_business_payload(payload: dict[str, Any], messages: list[BaseMessage]) -> SafeConversationFacts:
    """Turn one guard-approved business capability result into safe prose facts."""
    capability = str(payload.get("capability") or "health_overview")
    subject = str(payload.get("subject_label") or "你")
    period = _period_label_from_value(payload.get("period"))
    raw_facts = payload.get("facts") if isinstance(payload.get("facts"), dict) else {}
    facts: list[str] = []

    profile = raw_facts.get("profile")
    if isinstance(profile, dict) and profile.get("available"):
        facts.append("系统内有基础健康档案信息")
    blood_pressure = raw_facts.get("blood_pressure")
    if isinstance(blood_pressure, dict):
        count = _as_number(blood_pressure.get("record_count")) or 0
        if count:
            facts.append(f"{period}共记录 {int(count)} 次血压")
            if blood_pressure.get("latest"):
                facts.append(f"最近一次血压是 {blood_pressure['latest']}")
            if blood_pressure.get("average"):
                facts.append(f"已记录数值平均约为 {blood_pressure['average']}")
        else:
            facts.append(f"{period}暂无血压记录")
    for key, label in (("metrics", "健康指标"), ("sleep_duration", "睡眠"), ("weight", "体重"), ("steps", "步数"), ("heart_rate", "心率"), ("symptoms", "症状记录"), ("medical_events", "健康事件"), ("documents", "医疗资料"), ("alerts", "提醒")):
        value = raw_facts.get(key)
        if not isinstance(value, dict):
            continue
        count = _as_number(value.get("record_count")) or 0
        if key in {"sleep_duration", "weight", "steps", "heart_rate"} and value.get("latest") is not None:
            unit = _display_unit(str(value.get("unit") or ""))
            facts.append(f"最近一次{label}记录为 {_format_number(value['latest'])} {unit}".strip())
        elif count:
            facts.append(f"相关{label}共有 {int(count)} 条")
        else:
            facts.append(f"{period}暂无{label}")
    unavailable = tuple(str(item) for item in payload.get("unavailable_sections", []) if isinstance(item, str))
    if not facts and unavailable:
        facts.append("本次请求的部分系统记录暂不可用，未显示任何推测结果")
    elif not facts:
        facts.append("系统内暂时没有可用于本次整理的相关记录")
    topic = "health_overview" if capability == "health_overview" else (str(payload.get("metric") or capability))
    return SafeConversationFacts(
        topic=topic,
        subject=subject,
        period=period,
        facts=tuple(facts[:12]),
        unavailable=unavailable,
        next_actions=_next_actions(topic),
        boundary_required=not _has_recent_health_boundary(messages),
    )


def _composer_messages(*, history: list[BaseMessage], user_question: str, facts: SafeConversationFacts) -> list[LLMMessage]:
    messages = [
        LLMMessage(
            role="system",
            content=f"{CONVERSATION_PERSONA_GUIDANCE}\n\n{COMPOSER_SYSTEM_PROMPT}",
        )
    ]
    for message in _recent_visible_history(history):
        if isinstance(message, HumanMessage):
            messages.append(LLMMessage(role="user", content=_clip(str(message.content), 320)))
        elif isinstance(message, AIMessage) and not message.tool_calls:
            messages.append(LLMMessage(role="assistant", content=_clip(str(message.content), 480)))
    payload = json.dumps(facts.as_prompt_payload(), ensure_ascii=False, separators=(",", ":"))
    messages.append(
        LLMMessage(
            role="user",
            content=(
                "请只依据下面安全事实包回答当前问题。不要暴露内部字段或工具名称。\n"
                f"当前问题：{_clip(user_question, 320)}\n安全事实包：{payload}"
            ),
        )
    )
    return messages


def _recent_visible_history(history: list[BaseMessage]) -> list[BaseMessage]:
    visible = [item for item in history if isinstance(item, (HumanMessage, AIMessage)) and not isinstance(item, ToolMessage)]
    # The newest human message is represented again as the explicit question.
    return visible[-7:-1] if visible and isinstance(visible[-1], HumanMessage) else visible[-6:]


def _facts_for_tool(*, tool: str, summary: dict[str, Any], count: int | float | None, plan: dict[str, Any]) -> list[str]:
    numeric_count = int(count or 0)
    if tool == "health_data.blood_pressure.summary":
        systolic, diastolic = summary.get("latest_systolic"), summary.get("latest_diastolic")
        facts = [f"{_period_label(plan)}共记录 {numeric_count} 次血压"]
        if _is_numeric(systolic) and _is_numeric(diastolic):
            facts.append(f"最近一次血压是 {_format_number(systolic)}/{_format_number(diastolic)} mmHg")
        avg_systolic, avg_diastolic = summary.get("avg_systolic"), summary.get("avg_diastolic")
        if _is_numeric(avg_systolic) and _is_numeric(avg_diastolic):
            facts.append(f"已记录数值平均约为 {_format_number(avg_systolic)}/{_format_number(avg_diastolic)} mmHg")
        return facts
    if tool == "health_data.metric.summary":
        metric = _metric_label(str(summary.get("metric_type") or plan.get("metric_type") or ""))
        facts = [f"{metric}共有 {numeric_count} 条记录"]
        value = summary.get("latest_value")
        if _is_numeric(value):
            unit = _display_unit(str(summary.get("unit") or ""))
            facts.append(f"最近一次{metric}为 {_format_number(value)} {unit}".strip())
        average = summary.get("avg_value")
        if _is_numeric(average):
            unit = _display_unit(str(summary.get("unit") or ""))
            facts.append(f"已记录{metric}平均约为 {_format_number(average)} {unit}".strip())
        return facts
    if tool == "health_data.metrics.recent":
        return [f"最近整理到 {numeric_count} 条健康指标记录"]
    if tool == "health_record.symptoms.query":
        return [f"相关症状记录共有 {numeric_count} 条"]
    if tool == "medical_timeline.events.query":
        return [f"相关健康事件共有 {numeric_count} 条"]
    if tool == "documents.query":
        return [f"相关医疗资料共有 {numeric_count} 份"]
    if tool == "alerts.query":
        return [f"相关提醒共有 {numeric_count} 条"]
    if tool == "health_profile.get":
        return ["系统内有基础健康档案信息"]
    return [f"相关系统记录共有 {numeric_count} 条"]


def _empty_fact_for_tool(tool: str, plan: dict[str, Any]) -> str:
    if tool == "health_data.blood_pressure.summary":
        return f"{_period_label(plan)}暂无血压记录"
    if tool == "health_data.metric.summary":
        return f"{_period_label(plan)}暂无{_metric_label(str(plan.get('metric_type') or ''))}记录"
    return "系统内暂无相关记录"


def _topic_label(intent: str, results: list[Any]) -> str:
    if intent == "query_daily_status":
        return "health_overview"
    if intent == "query_blood_pressure" or any(isinstance(item, dict) and item.get("tool") == "health_data.blood_pressure.summary" for item in results):
        return "blood_pressure"
    if intent == "query_metrics":
        return "health_metric"
    return "health_records"


def _next_actions(topic: str) -> tuple[str, ...]:
    if topic == "blood_pressure":
        return ("查看最近30天变化", "查看其他健康记录")
    if topic == "health_metric":
        return ("查看最近30天变化", "查看其他健康指标")
    if topic == "health_overview":
        return ("查看血压记录", "查看睡眠记录")
    return ("查看近期变化",)


def _period_label(plan: dict[str, Any]) -> str:
    label = str(plan.get("time_range_label") or "")
    if label:
        return label
    days = _as_number(plan.get("days"))
    return f"最近{int(days)}天" if days else "这段时间"


def _period_label_from_value(value: Any) -> str:
    mapping = {"7d": "最近7天", "30d": "最近30天", "90d": "最近90天", "365d": "最近一年"}
    return mapping.get(str(value or ""), "这段时间")


def _has_recent_health_boundary(messages: list[BaseMessage]) -> bool:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and not message.tool_calls:
            return "不替代医生判断" in str(message.content)
    return False


def _latest_tool_payload(messages: list[BaseMessage]) -> dict[str, Any] | None:
    for message in reversed(messages):
        if isinstance(message, ToolMessage):
            try:
                payload = json.loads(str(message.content))
            except (TypeError, ValueError):
                return None
            return payload if isinstance(payload, dict) else None
    return None


def _is_grounded(content: str, facts: SafeConversationFacts) -> bool:
    # The model may paraphrase prose, but numeric record facts must survive.
    required_numbers = re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?", " ".join(facts.facts))
    return not required_numbers or any(number in content for number in required_numbers)


def _clean_content(value: Any) -> str:
    return _clip(str(value or "").strip(), 1600)


def _clip(value: str, length: int) -> str:
    return value.replace("\x00", " ").strip()[:length]


def _as_number(value: Any) -> int | float | None:
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _is_numeric(value: Any) -> bool:
    return _as_number(value) is not None


def _format_number(value: Any) -> str:
    return f"{float(value):.0f}" if float(value).is_integer() else f"{float(value):.1f}"


def _metric_label(value: str) -> str:
    return {"sleep_duration": "睡眠", "steps": "步数", "weight": "体重", "heart_rate": "心率", "bmi": "BMI"}.get(value, "健康指标")


def _display_unit(value: str) -> str:
    return {"hour": "小时", "hours": "小时"}.get(value.strip().lower(), value)
