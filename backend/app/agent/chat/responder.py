from __future__ import annotations

from typing import Any

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
        safe_facts: str = "",
        fallback_answer: str | None = None,
    ) -> str:
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
                    safe_facts=safe_facts,
                ),
                temperature=min(max(self.settings.LLM_TEMPERATURE, 0.2), 0.7),
                max_tokens=min(self.settings.LLM_MAX_TOKENS, 500),
                metadata={"workflow_type": "chat_workflow", "conversation_intent": intent.value},
            )
            content = (response.content or "").strip()
            if not content or not _contains_cjk(content):
                return fallback
            if self.safety_policy.evaluate_output(content, workflow_type="chat_workflow").blocked:
                return fallback
            if intent in {ConversationIntent.HEALTH_RECORD_QUERY, ConversationIntent.FAMILY_HEALTH_QUERY}:
                content = _preserve_record_facts(content, safe_facts)
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
        safe_facts: str,
    ) -> list[LLMMessage]:
        system_prompt = _system_prompt(intent)
        context_parts: list[str] = []
        if session_summary:
            context_parts.append("近期对话摘要（仅用于承接语境，不能当作健康事实）：\n" + "\n".join(session_summary[-6:]))
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


def _fallback_response(intent: ConversationIntent, message: str) -> str:
    text = (message or "").strip()
    if intent == ConversationIntent.OTHER:
        return "我目前不能查询实时天气或外部资讯。不过我可以陪你聊聊，也可以在权限允许的范围内整理自己和家人的健康记录。"
    if intent == ConversationIntent.HEALTH_KNOWLEDGE:
        if "感冒" in text:
            return "感冒后的不适持续时间会因人和具体情况不同而不同。可以留意休息、补水和症状变化；如果不适加重、持续不缓解或出现明显不适，建议咨询医生。"
        return "睡眠会受到作息、压力、环境、咖啡因摄入和身体不适等多种因素影响。可以先留意这些日常因素；如果困扰持续或伴随明显不适，建议咨询医生。"
    if "你是谁" in text or "介绍" in text:
        return "我是你的 AI 健康管家，可以陪你聊天，也可以在权限允许的范围内帮你整理自己或家人的健康记录。"
    if any(term in text.lower() for term in ("你好", "嗨", "hello", "hi", "hey")):
        return "你好，很高兴和你聊聊。今天过得怎么样？想看看健康记录时，也可以直接告诉我。"
    return "我在。你可以和我聊聊近况，也可以问我已记录的睡眠、血压、提醒、资料或家庭健康信息。"


def _contains_cjk(value: str) -> bool:
    return any("\u4e00" <= character <= "\u9fff" for character in value)
