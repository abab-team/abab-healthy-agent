from __future__ import annotations

import re
from typing import Any

from app.agent.chat.insights import explain_blood_pressure_reference
from app.agent.chat.router import ConversationIntent
from app.agent.safety import AgentSafetyPolicy
from app.core.config import Settings, get_settings
from app.llm.client import LLMClient, get_llm_client
from app.llm.schemas import LLMMessage


class ConversationResponder:
    """Natural-language layer with no database, tool, or identity authority."""

    def __init__(self, *, settings: Settings | None = None, llm_client: LLMClient | Any | None = None) -> None:
        self.settings = settings or get_settings()
        self.llm_client = llm_client
        self.safety_policy = AgentSafetyPolicy()

    def respond(
        self,
        *,
        intent: ConversationIntent,
        user_message: str,
        session_summary: tuple[str, ...] = (),
        assistant_context: tuple[str, ...] = (),
        safe_facts: str = "",
        fallback_answer: str | None = None,
    ) -> str:
        contextual_reply = _contextual_conversation_reply(user_message, assistant_context)
        if contextual_reply:
            return contextual_reply
        fallback = fallback_answer or _fallback_response(intent, user_message)
        if intent == ConversationIntent.OTHER:
            return fallback
        if not self.settings.LLM_ENABLED or not self.settings.LLM_CHAT_ENABLED:
            return fallback
        try:
            client = self.llm_client or get_llm_client(self.settings)
            response = client.chat(
                self._messages(
                    intent=intent,
                    user_message=user_message,
                    session_summary=session_summary,
                    assistant_context=assistant_context,
                    safe_facts=safe_facts,
                ),
                temperature=min(max(self.settings.LLM_TEMPERATURE, 0.2), 0.7),
                max_tokens=min(self.settings.LLM_MAX_TOKENS, 500),
                metadata={"workflow_type": "chat_workflow", "conversation_intent": intent.value},
            )
            content = (response.content or "").strip()
            if not content or not _is_chinese_response(content):
                return fallback
            if self.safety_policy.evaluate_output(content, workflow_type="chat_workflow").blocked:
                return fallback
            if intent in {ConversationIntent.HEALTH_RECORD_QUERY, ConversationIntent.FAMILY_HEALTH_QUERY}:
                content = _preserve_record_facts(content, safe_facts)
                return content
            if intent in {ConversationIntent.HEALTH_RECORD_QUERY, ConversationIntent.FAMILY_HEALTH_QUERY} and "根据系统内记录" not in content:
                content = content.rstrip() + "\n\n以上根据系统内记录整理，不替代医生判断。"
            if intent == ConversationIntent.HEALTH_KNOWLEDGE:
                content = _ensure_knowledge_topic(content, user_message)
            return content
        except Exception:
            return fallback

    def _messages(
        self,
        *,
        intent: ConversationIntent,
        user_message: str,
        session_summary: tuple[str, ...],
        assistant_context: tuple[str, ...],
        safe_facts: str,
    ) -> list[LLMMessage]:
        system_prompt = _system_prompt(intent)
        context_parts: list[str] = []
        if session_summary:
            context_parts.append("近期对话摘要（仅用于承接语境，不能当作健康事实）：\n" + "\n".join(session_summary[-6:]))
        if assistant_context:
            context_parts.append("受控会话上下文（不包含标识符或健康事实）：\n" + "\n".join(assistant_context[:6]))
        if safe_facts:
            context_parts.append("已鉴权的系统记录事实：\n" + safe_facts[:1800])
        context_parts.append("用户这次说：\n" + user_message[:500])
        return [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content="\n\n".join(context_parts)),
        ]


def _preserve_record_facts(content: str, safe_facts: str) -> str:
    """Keep approved tool facts when a prose model makes an answer too terse.

    The model may rephrase the opening, but it must not silently discard a
    permitted record category from an overview. `safe_facts` is already a
    bounded, de-identified ToolExecutor summary.
    """
    # A substantive LLM response may paraphrase approved facts. Do not turn it
    # into a raw tool dump merely because the wording is not byte-for-byte.
    if len(content.strip()) >= 120:
        return content
    fact_lines = [line.strip() for line in safe_facts.splitlines() if line.strip()]
    missing = [line for line in fact_lines if line not in content]
    if not missing:
        return content
    return content.rstrip() + "\n\n已整理的记录：\n" + "\n".join(f"- {line}" for line in missing)


def _ensure_knowledge_topic(content: str, user_message: str) -> str:
    """Keep a health-knowledge reply anchored to the user's stated topic."""
    if "睡" in user_message and "睡眠" not in content:
        return content.rstrip() + "\n\n睡眠也会受到这些日常因素影响。"
    return content


def _system_prompt(intent: ConversationIntent) -> str:
    shared = (
        "你是 Family Health Agent 的家庭健康管家。说话自然、温和、简洁，使用简体中文。"
        "你不是医生，不诊断、不处方、不提供剂量或停药建议，也不作绝对健康判断。"
        "不要提及工具、数据库、模型、提示词或内部流程。"
    )
    if intent in {ConversationIntent.HEALTH_RECORD_QUERY, ConversationIntent.FAMILY_HEALTH_QUERY}:
        return shared + "只依据给你的已鉴权系统记录事实回答；不要补充未提供的数值。结尾用一句简短提示说明内容基于系统内记录，不替代医生判断。"
    if intent == ConversationIntent.HEALTH_KNOWLEDGE:
        return shared + "这是一般健康科普，不读取或推断用户个人健康数据。用通俗语言解释可能的常见因素，并建议持续不适时咨询医生。"
    return shared + "这是普通对话。自然回应用户；只有谈到健康记录时才说明可以协助整理。"


def _contextual_conversation_reply(message: str, assistant_context: tuple[str, ...]) -> str | None:
    """Answer identity and continuity turns from controlled context only."""
    text = (message or "").strip()
    if _is_identity_question(text):
        name = _current_user_name(assistant_context)
        if name:
            return (
                f"\u4f60\u662f {name}\u3002\u8fd9\u6b21\u5bf9\u8bdd\u4f1a\u4ee5\u4f60\u5f53\u524d\u767b\u5f55\u7684\u8eab\u4efd\u6765\u6574\u7406\u8bb0\u5f55\uff1b"
                "\u9700\u8981\u65f6\uff0c\u4e5f\u53ef\u4ee5\u6309\u5bb6\u5ead\u5171\u4eab\u6743\u9650\u67e5\u770b\u5bb6\u4eba\u8d44\u6599\u3002"
            )
        return "\u4f60\u662f\u6b63\u5728\u4f7f\u7528\u8fd9\u4e2a\u5bb6\u5ead\u8d26\u53f7\u7684\u7528\u6237\u3002"
    if _is_context_challenge(text):
        return (
            "\u8bb0\u5f97\u3002\u8fd9\u6b21\u5bf9\u8bdd\u4f1a\u627f\u63a5\u521a\u624d\u5df2\u786e\u8ba4\u7684\u67e5\u8be2\u4e0a\u4e0b\u6587\u3002"
            "\u4f60\u53ef\u4ee5\u76f4\u63a5\u7ee7\u7eed\u95ee\u201c\u90a3\u4e0a\u4e2a\u6708\u5462\u201d\u6216\u201c\u90a3\u8840\u538b\u5462\u201d\u3002"
        )
    if reference_reply := explain_blood_pressure_reference(text):
        return reference_reply
    if _is_health_interpretation_question(text):
        return (
            "\u53ef\u4ee5\u3002\u8bf7\u628a\u5177\u4f53\u6570\u503c\u548c\u6307\u6807\u53d1\u7ed9\u6211\uff08\u4f8b\u5982 118/76 mmHg\uff09\uff0c"
            "\u6211\u53ef\u4ee5\u8bf4\u660e\u5e38\u89c1\u6210\u4eba\u53c2\u8003\u533a\u95f4\uff0c\u5e76\u5e2e\u4f60\u56de\u770b\u5df2\u8bb0\u5f55\u7684\u8d8b\u52bf\u3002"
            "\u5355\u6b21\u8bb0\u5f55\u4e0d\u4ee3\u8868\u6574\u4f53\u5065\u5eb7\u60c5\u51b5\u3002"
        )
    return None


def _current_user_name(assistant_context: tuple[str, ...]) -> str | None:
    pattern = re.compile(r"^\u5f53\u524d\u7528\u6237\u79f0\u547c:\s*(.+)$")
    for item in assistant_context:
        match = pattern.match(item.strip())
        if match:
            return match.group(1).strip() or None
    return None


def _is_identity_question(text: str) -> bool:
    return text in {"\u6211\u662f\u8c01", "\u6211\u53eb\u4ec0\u4e48", "\u6211\u7684\u540d\u5b57"}


def _is_context_challenge(text: str) -> bool:
    return any(
        phrase in text
        for phrase in (
            "\u4f60\u4e0d\u662f\u8bfb\u8fc7\u4e86\u5417",
            "\u4f60\u4e0d\u662f\u8bf4\u8fc7\u5417",
            "\u521a\u624d\u4e0d\u662f",
            "\u4f60\u8bb0\u5f97\u5417",
        )
    )


def _is_health_interpretation_question(text: str) -> bool:
    return any(
        phrase in text
        for phrase in (
            "\u8fd9\u4e2a\u6570\u503c\u5065\u5eb7\u5417",
            "\u8fd9\u4e2a\u6570\u636e\u5065\u5eb7\u5417",
            "\u6b63\u5e38\u5417",
            "\u5f02\u5e38\u5417",
            "\u6709\u95ee\u9898\u5417",
            "\u4e25\u91cd\u5417",
        )
    )


def _fallback_response(intent: ConversationIntent, message: str) -> str:
    text = (message or "").strip()
    if intent == ConversationIntent.OTHER:
        return "我目前不能查询实时天气或外部资讯。不过我可以陪你聊聊，也可以在权限允许的范围内整理自己和家人的健康记录。"
    if intent == ConversationIntent.HEALTH_KNOWLEDGE:
        if reference_reply := explain_blood_pressure_reference(text):
            return reference_reply
        if any(term in text for term in ("\u8fd9\u4e2a\u6570\u503c", "\u8fd9\u4e2a\u6570\u636e", "\u6b63\u5e38\u5417", "\u5f02\u5e38\u5417", "\u4e25\u91cd\u5417")):
            return (
                "\u8bf7\u628a\u5177\u4f53\u6307\u6807\u548c\u6570\u503c\u53d1\u7ed9\u6211\uff0c\u6211\u53ef\u4ee5\u8bf4\u660e\u5e38\u89c1\u6210\u4eba\u53c2\u8003\u533a\u95f4\uff0c"
                "\u5e76\u5e2e\u4f60\u56de\u770b\u6700\u8fd1\u8bb0\u5f55\u7684\u53d8\u5316\u3002\u5355\u6b21\u8bb0\u5f55\u4e0d\u4ee3\u8868\u6574\u4f53\u5065\u5eb7\u60c5\u51b5\u3002"
            )
        if "感冒" in text:
            return "感冒后的不适持续时间会因人和具体情况不同而不同。可以留意休息、补水和症状变化；如果不适加重、持续不缓解或出现明显不适，建议咨询医生。"
        return "睡眠会受到作息、压力、环境、咖啡因摄入和身体不适等多种因素影响。可以先留意这些日常因素；如果困扰持续或伴随明显不适，建议咨询医生。"
    if "你是谁" in text or "介绍" in text:
        return "我是你的 AI 健康管家，可以陪你聊天，也可以在权限允许的范围内帮你整理自己或家人的健康记录。"
    if any(term in text.lower() for term in ("你好", "嗨", "hello", "hi", "hey")):
        return "你好，很高兴和你聊聊。今天过得怎么样？想看看健康记录时，也可以直接告诉我。"
    return "我在。你可以和我聊聊近况，也可以问我已记录的睡眠、血压、提醒、资料或家庭健康信息。"


def _is_chinese_response(value: str) -> bool:
    """Reject provider fallbacks that are mostly English in this Chinese UI."""
    cjk_count = sum("\u4e00" <= character <= "\u9fff" for character in value)
    latin_count = sum(character.isascii() and character.isalpha() for character in value)
    return cjk_count >= 4 and cjk_count * 2 >= latin_count
