"""Conversation Runtime V3: a checkpointed, tool-calling Agent loop.

The graph deliberately has no keyword router.  The Agent node either replies
naturally or emits one constrained business-capability call.  A server-owned
guard resolves people and permissions, then the existing ToolExecutor performs
the underlying reads and returns a redacted ToolMessage to the Agent.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import time
from typing import Any, Callable
from uuid import UUID

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import RemoveMessage

from app.agent.conversation_v2.business_tool_runtime import ALLOWED_CAPABILITIES, ConversationBusinessToolRuntime
from app.agent.conversation_v2.checkpointer import PersistentConversationCheckpointer, get_persistent_checkpointer
from app.agent.conversation_v2.message_safety import sanitize_checkpoint_message
from app.agent.conversation.quick_note_service import validate_candidate
from app.agent.conversation_v2.response_composer import ConversationResponseComposer, build_safe_conversation_facts
from app.agent.conversation_v2.response_composer import (
    has_disallowed_assurance,
    remove_disallowed_assurance_sentences,
    remove_disallowed_medical_sentences,
    safe_conversation_replacement,
)
from app.agent.persona import CONVERSATION_PERSONA_GUIDANCE
from app.agent.safety import AgentSafetyPolicy
from app.agent.conversation_v2.state import ConversationState
from app.core.config import Settings, get_settings
from app.llm.client import LLMClient, get_llm_client
from app.llm.schemas import LLMMessage


SYSTEM_PROMPT = """你是家庭健康管家：温和、自然、简洁，能聊天，也能在授权范围内整理自己和家人的健康记录。

你只可以根据对话中已经出现的 ToolMessage 事实回答健康记录问题；不要编造事实、诊断、确诊、处方、剂量或停药建议。你不能查询实时天气。只有服务器已开启随手记模式，或用户明确要求“记录、记下来、保存”时，才可以提出待确认草稿候选；候选绝不是正式记录，也不能声称已经保存。

你可以且只能在需要读取已授权健康记录时调用以下业务能力，不得暴露任何内部工具名：
- health_overview(subject_reference, period): 综合已授权记录。
- metric_detail(subject_reference, metric, period): metric 只能是 blood_pressure、sleep、weight、steps、heart_rate、bmi。
- medical_history(subject_reference, period)
- document_overview(subject_reference, period)
- alert_overview(subject_reference, period)

当需要工具时，严格只输出 JSON：
{"type":"tool_call","name":"metric_detail","arguments":{"subject_reference":"self","metric":"blood_pressure","period":"7d"}}
当不需要工具时，严格只输出 JSON：
{"type":"final","content":"自然、简洁的中文回复"}
当需要提出待确认草稿时，严格只输出 JSON：
{"type":"draft_candidate","candidate":{"candidate_type":"symptom|metric|medical_event|alert","summary":"简短内容","occurred_at_hint":"可选时间提示","duration_hint":"可选持续时间","details":"安全的简短补充"}}
metric 草稿必须额外有 metric_type、value（数字）和 unit。只有 symptom、metric、medical_event、alert 四类候选可用。
如果刚刚已有相关 ToolMessage，优先利用其中事实，不要重复调用。对健康知识可以做一般性科普，但不读取个人数据，也不做个体诊断。"""
TOOL_CALL_POLICY = """
Mandatory tool protocol:
- When a user asks about recorded health information for themselves or a named family member, you MUST emit exactly one allowed tool_call before answering. This includes an overall recent health question, blood pressure, sleep, weight, steps, heart rate, BMI, medical history, documents, and alerts.
- For a named relative, pass the relation or name the user used as subject_reference, for example "father" or the Chinese relation they wrote. The server resolves the real member and permissions.
- Never claim that a user's or family member's records are unavailable, absent, restricted, or incomplete unless a ToolMessage for that request has already supplied that fact.
- Do not turn a health-record request into a generic conversation response. If existing ToolMessage facts answer a follow-up, use those facts without another tool call.
- Health knowledge and casual chat can answer naturally without a tool when they do not ask for a person's recorded data.
- Do not claim that a person is healthy, stable, fine, or can rest assured. You may compare a recorded value with a common adult reference, while making clear that one record is not a diagnosis or a guarantee.
- Avoid equivalent Chinese assurance wording such as "让人放心"、"可以放心"、"整体平稳"、"没有问题" or "身体很好" when describing a person's health records.
"""


@dataclass(frozen=True)
class ConversationTurnResult:
    thread_id: str
    answer: str
    messages: tuple[BaseMessage, ...]
    tool_calls_count: int = 0
    conversation_task: dict[str, Any] | None = None


class ConversationAccessDeniedError(PermissionError):
    """Raised before a checkpoint can be read for a different user."""


class ConversationRuntimeV2:
    """The single V3 conversation entry point, retained under its stable name."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        checkpointer: PersistentConversationCheckpointer | None = None,
        owner_resolver: Callable[[str], UUID | None] | None = None,
        llm_client: LLMClient | None = None,
        tool_runtime: ConversationBusinessToolRuntime | None = None,
        draft_candidate_creator: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None,
        user_context: dict[str, str] | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.checkpointer = checkpointer or get_persistent_checkpointer(self.settings.CONVERSATION_RUNTIME_V2_CHECKPOINT_PATH)
        self.owner_resolver = owner_resolver
        self.llm_client = llm_client or get_llm_client(self.settings)
        self.tool_runtime = tool_runtime
        self.draft_candidate_creator = draft_candidate_creator
        self.user_context = dict(user_context or {})
        self.response_composer = ConversationResponseComposer(settings=self.settings, llm_client=self.llm_client)
        self.safety = AgentSafetyPolicy()
        self.graph = self._build_graph()

    def run_turn(self, *, session_id: UUID | str, user_id: UUID, user_message: str, request_id: str | None = None, quick_note_mode: bool = False) -> ConversationTurnResult:
        thread_id = str(session_id)
        self._assert_session_owner(thread_id, user_id)
        config = {"configurable": {"thread_id": thread_id}}
        safe_message = sanitize_checkpoint_message(user_message) or "[empty message]"
        with self.checkpointer.lock_thread(thread_id):
            snapshot = self.graph.get_state(config)
            safe_request_id = _safe_request_id(request_id)
            if safe_request_id and safe_request_id in snapshot.values.get("processed_request_ids", []):
                messages = tuple(snapshot.values.get("messages", ()))
                return ConversationTurnResult(thread_id, _latest_ai_content(messages), messages, 0)
            messages: list[BaseMessage] = []
            if not snapshot.values.get("messages"):
                display_name = self.user_context.get("name", "")[:80]
                base_prompt = f"{CONVERSATION_PERSONA_GUIDANCE}\n\n{SYSTEM_PROMPT}\n\n{TOOL_CALL_POLICY}"
                messages.append(SystemMessage(content=f"{base_prompt}\n当前用户显示名：{display_name}。" if display_name else base_prompt))
            messages.append(HumanMessage(content=safe_message))
            processed = list(snapshot.values.get("processed_request_ids", []))
            if safe_request_id:
                processed = [*processed[-19:], safe_request_id]
            state = self.graph.invoke(
                {
                    "messages": messages,
                    "processed_request_ids": processed,
                    "pending_tool_calls": [],
                    "validated_tool_calls": [],
                    "tool_execution_results": [],
                    "runtime_metadata": {"user_name": self.user_context.get("name", "")[:80], "tool_calls_count": 0, "quick_note_mode": bool(quick_note_mode)},
                },
                config=config,
            )
        final_messages = tuple(state.get("messages", ()))
        metadata = state.get("runtime_metadata") or {}
        conversation_task = metadata.get("conversation_task")
        candidate = metadata.get("draft_candidate")
        if isinstance(candidate, dict) and self.draft_candidate_creator is not None:
            try:
                conversation_task = self.draft_candidate_creator(candidate)
            except Exception:
                conversation_task = None
        return ConversationTurnResult(thread_id, _latest_ai_content(final_messages), final_messages, int(metadata.get("tool_calls_count") or 0), conversation_task if isinstance(conversation_task, dict) else None)

    def get_messages(self, *, session_id: UUID | str, user_id: UUID) -> tuple[BaseMessage, ...]:
        thread_id = str(session_id)
        self._assert_session_owner(thread_id, user_id)
        with self.checkpointer.lock_thread(thread_id):
            return tuple(self.graph.get_state({"configurable": {"thread_id": thread_id}}).values.get("messages", ()))

    def close(self) -> None:
        self.checkpointer.close()

    def _assert_session_owner(self, thread_id: str, user_id: UUID) -> None:
        if self.owner_resolver is not None and self.owner_resolver(thread_id) != user_id:
            raise ConversationAccessDeniedError("conversation session is not available")

    def _build_graph(self):
        graph = StateGraph(ConversationState)
        graph.add_node("load_context", self._load_context)
        graph.add_node("agent", self._agent)
        graph.add_node("tool_guard", self._tool_guard)
        graph.add_node("execute_business_tool", self._execute_business_tool)
        graph.add_node("compose_response", self._compose_response)
        graph.add_node("output_safety", self._output_safety)
        graph.add_edge(START, "load_context")
        graph.add_edge("load_context", "agent")
        graph.add_conditional_edges("agent", self._agent_next, {"tool_guard": "tool_guard", "output_safety": "output_safety"})
        graph.add_conditional_edges("tool_guard", self._guard_next, {"execute_business_tool": "execute_business_tool", "agent": "agent"})
        graph.add_edge("execute_business_tool", "compose_response")
        graph.add_edge("compose_response", "output_safety")
        graph.add_edge("output_safety", END)
        return graph.compile(checkpointer=self.checkpointer.saver)

    def _load_context(self, state: ConversationState) -> dict[str, Any]:
        # Context is deliberately labels only. The guard resolves actual member
        # IDs and permissions only after a constrained tool call is requested.
        return {"runtime_metadata": {**dict(state.get("runtime_metadata") or {}), "runtime": "v3", "available_capabilities": ",".join(sorted(ALLOWED_CAPABILITIES))}}

    def _agent(self, state: ConversationState) -> dict[str, Any]:
        messages = _messages_after_trim(list(state.get("messages", ())), _trim_messages(list(state.get("messages", ())), self.settings.CONVERSATION_RUNTIME_V2_MAX_MESSAGES))
        raw = self._ask_agent(messages, conversation_context=state.get("conversation_context"), quick_note_mode=bool((state.get("runtime_metadata") or {}).get("quick_note_mode")))
        decision = _parse_agent_decision(raw)
        if decision.get("type") == "draft_candidate":
            enabled = bool((state.get("runtime_metadata") or {}).get("quick_note_mode"))
            user_message = next((str(item.content) for item in reversed(messages) if isinstance(item, HumanMessage)), "")
            explicit = bool(re.search(r"(帮我)?(记录|记下来|保存这条|存一下)", user_message))
            try:
                candidate = validate_candidate(decision.get("candidate") if isinstance(decision.get("candidate"), dict) else {})
            except ValueError:
                candidate = None
            if candidate and (enabled or explicit):
                return {"messages": [AIMessage(content="我帮你整理成了一条待确认记录，你可以先看一眼再决定是否保存。")], "runtime_metadata": {**dict(state.get("runtime_metadata") or {}), "agent_action": "final", "draft_candidate": candidate}}
        if decision.get("type") == "tool_call":
            call = {"id": f"business_{len(messages)}", "name": decision.get("name"), "args": decision.get("arguments")}
            return {"messages": [AIMessage(content="", tool_calls=[{**call, "type": "tool_call"}])], "pending_tool_calls": [call], "runtime_metadata": {**dict(state.get("runtime_metadata") or {}), "agent_action": "tool_call"}}
        answer = str(decision.get("content") or _safe_agent_failure())
        return {"messages": [AIMessage(content=sanitize_checkpoint_message(answer))], "runtime_metadata": {**dict(state.get("runtime_metadata") or {}), "agent_action": "final"}}

    def _agent_next(self, state: ConversationState) -> str:
        return "tool_guard" if (state.get("runtime_metadata") or {}).get("agent_action") == "tool_call" else "output_safety"

    def _tool_guard(self, state: ConversationState) -> dict[str, Any]:
        raw = next(iter(state.get("pending_tool_calls") or []), None)
        call = self.tool_runtime.validate(raw) if self.tool_runtime is not None and isinstance(raw, dict) else None
        if call is None:
            tool_id = str((raw or {}).get("id") or "invalid")
            return {"messages": [ToolMessage(content=json.dumps({"note": "该请求不能作为可用的只读能力执行。"}, ensure_ascii=False), tool_call_id=tool_id, name="tool_guard")], "validated_tool_calls": [], "runtime_metadata": {**dict(state.get("runtime_metadata") or {}), "guard_action": "blocked"}}
        return {"validated_tool_calls": [{"id": call.id, "name": call.name, "args": call.arguments}], "runtime_metadata": {**dict(state.get("runtime_metadata") or {}), "guard_action": "execute"}}

    def _guard_next(self, state: ConversationState) -> str:
        return "execute_business_tool" if state.get("validated_tool_calls") else "agent"

    def _execute_business_tool(self, state: ConversationState) -> dict[str, Any]:
        call_data = next(iter(state.get("validated_tool_calls") or []), None)
        call = self.tool_runtime.validate(call_data) if self.tool_runtime is not None and isinstance(call_data, dict) else None
        if call is None:
            return {"runtime_metadata": {**dict(state.get("runtime_metadata") or {}), "tool_calls_count": 0}}
        execution = self.tool_runtime.execute(call)
        payload = execution.tool_message
        metadata = {**dict(state.get("runtime_metadata") or {}), "tool_calls_count": int((state.get("runtime_metadata") or {}).get("tool_calls_count") or 0) + len(execution.underlying_results)}
        context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
        safe_context = {
            key: str(context[key])[:80]
            for key in ("subject_reference", "subject_label", "topic", "last_business_capability", "last_fact_type", "last_time_range")
            if isinstance(context.get(key), (str, int, float, bool))
        }
        return {
            "messages": [ToolMessage(content=json.dumps(payload, ensure_ascii=False, separators=(",", ":")), tool_call_id=call.id, name=call.name)],
            "tool_execution_results": [payload],
            "conversation_context": safe_context,
            "runtime_metadata": metadata,
        }

    def _compose_response(self, state: ConversationState) -> dict[str, Any]:
        messages = list(state.get("messages", ()))
        question = next((str(item.content) for item in reversed(messages) if isinstance(item, HumanMessage)), "")
        facts = build_safe_conversation_facts(state=state, messages=messages)
        fallback = _safe_fact_fallback(facts)
        result = self.response_composer.compose(
            history=messages,
            user_question=question,
            facts=facts,
            fallback_answer=fallback,
        )
        metadata = {
            **dict(state.get("runtime_metadata") or {}),
            "response_composer_used": result.llm_used,
            "response_composer_fallback": result.fallback_used,
        }
        return {"messages": [AIMessage(content=sanitize_checkpoint_message(result.content))], "runtime_metadata": metadata}

    def _output_safety(self, state: ConversationState) -> dict[str, Any]:
        messages = list(state.get("messages", ()))
        removals = _trim_messages(messages, self.settings.CONVERSATION_RUNTIME_V2_MAX_MESSAGES)
        latest = next((item for item in reversed(messages) if isinstance(item, AIMessage) and not item.tool_calls), None)
        if latest is None:
            return {"messages": removals}
        content = remove_disallowed_medical_sentences(str(latest.content or ""))
        if not content:
            replacement = AIMessage(id=latest.id, content=safe_conversation_replacement())
            return {"messages": [*removals, replacement]}
        decision = self.safety.evaluate_output(content, workflow_type="chat_workflow")
        if decision.blocked:
            replacement = AIMessage(id=latest.id, content=safe_conversation_replacement())
            return {"messages": [*removals, replacement]}
        if has_disallowed_assurance(content):
            cleaned = remove_disallowed_assurance_sentences(content)
            replacement = AIMessage(id=latest.id, content=cleaned or safe_conversation_replacement())
            return {"messages": [*removals, replacement]}
        return {"messages": removals}

    def _ask_agent(self, messages: list[BaseMessage], *, conversation_context: dict[str, Any] | None = None, quick_note_mode: bool = False) -> str:
        llm_messages = _to_llm_messages(messages, conversation_context=conversation_context)
        llm_messages.append(LLMMessage(role="system", content="随手记模式当前为开启。可对明确健康描述提出待确认草稿候选。" if quick_note_mode else "随手记模式当前为关闭。仅当用户明确要求记录、记下来或保存时，才可提出待确认草稿候选。"))
        # Keep mode guidance inside the initial system instruction so standard
        # conversation history remains system/user/assistant/user.
        if len(llm_messages) > 1 and llm_messages[0].role == "system" and llm_messages[-1].role == "system":
            llm_messages[0] = LLMMessage(role="system", content=f"{llm_messages[0].content}\n{llm_messages[-1].content}")
            llm_messages.pop()
        for attempt in range(2):
            try:
                response = self.llm_client.chat(
                    llm_messages,
                    temperature=0.2,
                    metadata={"conversation_runtime": "v3", "agent_mode": "business_tool_loop"},
                )
                return sanitize_checkpoint_message(response.content)
            except Exception:
                if attempt == 0:
                    time.sleep(0.8)
        return json.dumps({"type": "final", "content": _safe_agent_failure()}, ensure_ascii=False)


def _parse_agent_decision(raw: str) -> dict[str, Any]:
    text = str(raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`").replace("json\n", "", 1).strip()
    try:
        value = json.loads(text)
    except (TypeError, ValueError):
        return {"type": "final", "content": text or _safe_agent_failure()}
    if not isinstance(value, dict):
        return {"type": "final", "content": _safe_agent_failure()}
    if value.get("type") == "tool_call" and value.get("name") in ALLOWED_CAPABILITIES and isinstance(value.get("arguments"), dict):
        return value
    if value.get("type") == "final" and isinstance(value.get("content"), str):
        return value
    if value.get("type") == "draft_candidate" and isinstance(value.get("candidate"), dict):
        return value
    return {"type": "final", "content": _safe_agent_failure()}


def _to_llm_messages(messages: list[BaseMessage], *, conversation_context: dict[str, Any] | None = None) -> list[LLMMessage]:
    result: list[LLMMessage] = []
    for message in messages:
        if isinstance(message, SystemMessage):
            result.append(LLMMessage(role="system", content=str(message.content)))
        elif isinstance(message, HumanMessage):
            result.append(LLMMessage(role="user", content=str(message.content)))
        elif isinstance(message, ToolMessage):
            result.append(LLMMessage(role="user", content=f"已授权工具事实（只能依据此内容回答）：{message.content}"))
        elif isinstance(message, AIMessage) and not message.tool_calls:
            result.append(LLMMessage(role="assistant", content=str(message.content)))
    if conversation_context:
        payload = {
            key: value
            for key, value in conversation_context.items()
            if key in {"subject_reference", "subject_label", "topic", "last_business_capability", "last_fact_type", "last_time_range"}
        }
        if payload:
            result.append(LLMMessage(role="system", content=f"当前对话的服务器确认上下文（仅用于理解追问，不代表权限）：{json.dumps(payload, ensure_ascii=False)}"))
    return result


def _trim_messages(messages: list[BaseMessage], max_messages: int) -> list[RemoveMessage]:
    maximum = max(2, max_messages)
    if len(messages) <= maximum:
        return []
    systems = [item for item in messages if isinstance(item, SystemMessage)]
    capacity = max(1, maximum - len(systems))
    turns: list[list[BaseMessage]] = []
    current: list[BaseMessage] = []
    for item in (item for item in messages if not isinstance(item, SystemMessage)):
        if isinstance(item, HumanMessage) and current:
            turns.append(current)
            current = [item]
        else:
            current.append(item)
    if current:
        turns.append(current)
    kept: list[list[BaseMessage]] = []
    used = 0
    for turn in reversed(turns):
        if kept and used + len(turn) > capacity:
            break
        kept.append(turn)
        used += len(turn)
    keep = {item.id for item in [*systems, *[message for turn in reversed(kept) for message in turn]]}
    return [RemoveMessage(id=item.id) for item in messages if item.id not in keep]


def _messages_after_trim(messages: list[BaseMessage], removals: list[RemoveMessage]) -> list[BaseMessage]:
    removed = {item.id for item in removals}
    return [item for item in messages if item.id not in removed]


def _latest_ai_content(messages: tuple[BaseMessage, ...]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and not message.tool_calls:
            return str(message.content)
    return ""


def _safe_request_id(value: str | None) -> str | None:
    normalized = re.sub(r"[^A-Za-z0-9_.:-]", "", str(value or ""))[:100]
    return normalized or None


def _safe_agent_failure() -> str:
    return "我这会儿没能完成这次整理。你可以换一种说法再试，或稍后继续。"


def _safe_fact_fallback(facts) -> str:  # noqa: ANN001
    """A deterministic availability fallback used only when composition fails."""
    if facts.facts:
        text = f"我整理了{facts.subject}{facts.period}的已记录信息：" + "；".join(facts.facts[:4]) + "。"
    else:
        text = f"我暂时没有查到{facts.subject}{facts.period}可用于整理的相关记录。"
    return f"{text}\n\n内容基于系统内已有记录整理，不替代医生判断。"
