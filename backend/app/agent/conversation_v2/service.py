"""Message-native Conversation Runtime V2 with controlled read-only tools."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Callable
from uuid import UUID

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import RemoveMessage

from app.agent.conversation_v2.checkpointer import PersistentConversationCheckpointer, get_persistent_checkpointer
from app.agent.conversation_v2.message_safety import sanitize_checkpoint_message
from app.agent.conversation_v2.state import ConversationState
from app.agent.conversation_v2.tool_runtime import ConversationToolRuntime, safe_tool_result, tool_message_content
from app.core.config import Settings, get_settings
from app.llm.client import LLMClient, get_llm_client
from app.llm.schemas import LLMMessage


SYSTEM_PROMPT = (
    "You are a friendly family health assistant. You can chat naturally. "
    "For health-record questions, use only server-authorized tool facts supplied "
    "in the conversation. Never claim to browse databases, decide access, or give "
    "diagnosis, prescriptions, dosage, or medication-change advice."
)
_HEALTH_FOLLOW_UP_TERMS = ("这个数值健康吗", "这个数据健康吗", "这个健康吗", "健康吗", "正常吗", "异常吗")
_FRESH_DATA_TERMS = ("最新", "现在", "今天", "重新", "30天", "一个月", "上个月")


@dataclass(frozen=True)
class ConversationTurnResult:
    thread_id: str
    answer: str
    messages: tuple[BaseMessage, ...]
    tool_calls_count: int = 0


class ConversationAccessDeniedError(PermissionError):
    """Raised before a checkpoint can be read for a different user."""


class ConversationRuntimeV2:
    """A checkpointed graph whose only health-data path is ToolExecutor.

    The graph itself never creates a database session.  A workflow boundary
    injects ``ConversationToolRuntime`` for the current request; that adapter
    resolves family members and delegates every read to the existing executor.
    """

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        checkpointer: PersistentConversationCheckpointer | None = None,
        owner_resolver: Callable[[str], UUID | None] | None = None,
        llm_client: LLMClient | None = None,
        tool_runtime: ConversationToolRuntime | None = None,
        user_context: dict[str, str] | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.checkpointer = checkpointer or get_persistent_checkpointer(self.settings.CONVERSATION_RUNTIME_V2_CHECKPOINT_PATH)
        self.owner_resolver = owner_resolver
        self.llm_client = llm_client or get_llm_client(self.settings)
        self.tool_runtime = tool_runtime
        self.user_context = dict(user_context or {})
        self.graph = self._build_graph()

    def run_turn(
        self,
        *,
        session_id: UUID | str,
        user_id: UUID,
        user_message: str,
        request_id: str | None = None,
    ) -> ConversationTurnResult:
        thread_id = str(session_id)
        self._assert_session_owner(thread_id, user_id)
        safe_message = sanitize_checkpoint_message(user_message) or "[empty message]"
        config = {"configurable": {"thread_id": thread_id}}
        with self.checkpointer.lock_thread(thread_id):
            snapshot = self.graph.get_state(config)
            safe_request_id = _safe_request_id(request_id)
            if safe_request_id and safe_request_id in snapshot.values.get("processed_request_ids", []):
                messages = tuple(snapshot.values.get("messages", ()))
                return ConversationTurnResult(thread_id, _latest_ai_content(messages), messages, 0)

            new_messages: list[BaseMessage] = []
            if not snapshot.values.get("messages"):
                new_messages.append(SystemMessage(content=SYSTEM_PROMPT))
            new_messages.append(HumanMessage(content=safe_message))
            processed = list(snapshot.values.get("processed_request_ids", []))
            if safe_request_id:
                processed = [*processed[-19:], safe_request_id]
            state = self.graph.invoke(
                {
                    "messages": new_messages,
                    "processed_request_ids": processed,
                    "runtime_metadata": {"user_name": self.user_context.get("name", "")[:80]},
                },
                config=config,
            )
        messages = tuple(state.get("messages", ()))
        metadata = state.get("runtime_metadata") or {}
        return ConversationTurnResult(thread_id, _latest_ai_content(messages), messages, int(metadata.get("tool_calls_count") or 0))

    def get_messages(self, *, session_id: UUID | str, user_id: UUID) -> tuple[BaseMessage, ...]:
        thread_id = str(session_id)
        self._assert_session_owner(thread_id, user_id)
        with self.checkpointer.lock_thread(thread_id):
            snapshot = self.graph.get_state({"configurable": {"thread_id": thread_id}})
        return tuple(snapshot.values.get("messages", ()))

    def close(self) -> None:
        self.checkpointer.close()

    def _assert_session_owner(self, thread_id: str, user_id: UUID) -> None:
        if self.owner_resolver is None:
            return
        if self.owner_resolver(thread_id) != user_id:
            raise ConversationAccessDeniedError("conversation session is not available")

    def _build_graph(self):
        graph = StateGraph(ConversationState)
        graph.add_node("route", self._route)
        graph.add_node("plan", self._plan)
        graph.add_node("execute_tools", self._execute_tools)
        graph.add_node("respond", self._respond)
        graph.add_edge(START, "route")
        graph.add_conditional_edges("route", self._route_next, {"plan": "plan", "respond": "respond"})
        graph.add_conditional_edges("plan", self._plan_next, {"execute_tools": "execute_tools", "respond": "respond"})
        graph.add_edge("execute_tools", "respond")
        graph.add_edge("respond", END)
        return graph.compile(checkpointer=self.checkpointer.saver)

    def _route(self, state: ConversationState) -> dict[str, Any]:
        message = _latest_human_content(state.get("messages", ()))
        lowered = message.lower()
        if self.tool_runtime is not None and _is_health_follow_up(lowered) and not _requests_fresh_data(lowered):
            if _latest_tool_payload(state.get("messages", ())):
                return {"runtime_metadata": {**dict(state.get("runtime_metadata") or {}), "route": "tool_follow_up"}}
        if self.tool_runtime is not None and _may_be_record_query(message):
            return {"runtime_metadata": {**dict(state.get("runtime_metadata") or {}), "route": "health_query"}}
        return {"runtime_metadata": {**dict(state.get("runtime_metadata") or {}), "route": "chat"}}

    def _route_next(self, state: ConversationState) -> str:
        return "plan" if (state.get("runtime_metadata") or {}).get("route") == "health_query" else "respond"

    def _plan(self, state: ConversationState) -> dict[str, Any]:
        if self.tool_runtime is None:
            return {"pending_tool_calls": [], "runtime_metadata": {**dict(state.get("runtime_metadata") or {}), "route": "chat"}}
        planned = self.tool_runtime.plan(
            _latest_human_content(state.get("messages", ())),
            previous_plan_summary=state.get("plan_summary"),
        )
        calls = [{"id": call.id, "name": call.name, "args": dict(call.args)} for call in planned.calls]
        plan = planned.plan
        metadata = {
            **dict(state.get("runtime_metadata") or {}),
            "route": "health_query" if calls else "chat",
            "plan_reason": planned.reason or "accepted",
        }
        if plan is None or not calls:
            return {"pending_tool_calls": [], "plan_summary": {}, "runtime_metadata": metadata}
        ai_tool_call = AIMessage(
            content="",
            tool_calls=[{"id": call["id"], "name": call["name"], "args": call["args"], "type": "tool_call"} for call in calls],
        )
        return {
            "messages": [ai_tool_call],
            "pending_tool_calls": calls,
            "validated_tool_calls": calls,
            "plan_summary": {
                "intent": plan.intent.value,
                "member_label": plan.member_label,
                "member_scope": plan.member_scope,
                "metric_type": plan.metric_type,
                "time_range_label": plan.time_range.label,
                "days": plan.time_range.days,
            },
            "runtime_metadata": metadata,
        }

    def _plan_next(self, state: ConversationState) -> str:
        return "execute_tools" if state.get("validated_tool_calls") else "respond"

    def _execute_tools(self, state: ConversationState) -> dict[str, Any]:
        if self.tool_runtime is None:
            return {"tool_execution_results": [], "runtime_metadata": {**dict(state.get("runtime_metadata") or {}), "tool_calls_count": 0}}
        plan = self.tool_runtime.plan(
            _latest_human_content(state.get("messages", ())),
            previous_plan_summary=state.get("plan_summary"),
        ).plan
        # The plan must match the stored, server-validated shape.  Replacing it
        # would permit a new human message to alter a pending execution.
        stored = state.get("plan_summary") or {}
        if plan is None or plan.intent.value != stored.get("intent"):
            return {"tool_execution_results": [], "runtime_metadata": {**dict(state.get("runtime_metadata") or {}), "tool_calls_count": 0, "tool_error": "plan_changed"}}
        calls = list(state.get("validated_tool_calls") or [])
        results, permission = self.tool_runtime.execute(plan, calls)
        message_by_name = {str(call["name"]): str(call["id"]) for call in calls}
        tool_messages: list[ToolMessage] = []
        safe_results: list[dict[str, Any]] = []
        for result in results:
            safe = safe_tool_result(result)
            safe_results.append(safe)
            tool_messages.append(ToolMessage(content=tool_message_content(result), tool_call_id=message_by_name.get(result.tool_name, "unknown"), name=result.tool_name))
        metadata = {**dict(state.get("runtime_metadata") or {}), "tool_calls_count": len(results)}
        return {
            "messages": tool_messages,
            "tool_execution_results": safe_results,
            "permission_context": permission,
            "resolved_member_context": {"member": permission.get("member"), "allowed": permission.get("allowed")},
            "runtime_metadata": metadata,
        }

    def _respond(self, state: ConversationState) -> dict[str, Any]:
        messages = list(state.get("messages", ()))
        # A follow-up such as "这个数值健康吗" must inspect the persisted
        # ToolMessage before the ordinary history compactor can remove that
        # complete earlier tool turn.  The next ordinary turn compacts it.
        route = (state.get("runtime_metadata") or {}).get("route")
        removals = [] if route == "tool_follow_up" else _trim_messages(messages, self.settings.CONVERSATION_RUNTIME_V2_MAX_MESSAGES)
        visible = _messages_after_trim(messages, removals)
        if route == "tool_follow_up":
            answer = _interpret_latest_tool_fact(visible)
        elif state.get("tool_execution_results"):
            answer = _compose_tool_answer(state)
        else:
            answer = self._generate_chat_reply(visible)
        return {"messages": [*removals, AIMessage(content=sanitize_checkpoint_message(answer))]}

    def _generate_chat_reply(self, messages: list[BaseMessage]) -> str:
        if self.settings.LLM_ENABLED and self.settings.LLM_CHAT_ENABLED:
            llm_messages = _to_llm_messages(messages)
            try:
                content = sanitize_checkpoint_message(self.llm_client.chat(llm_messages, metadata={"conversation_runtime": "v2"}).content)
                if content:
                    return content
            except Exception:
                pass
        return _local_reply(messages, self.user_context.get("name", ""))


def _compose_tool_answer(state: ConversationState) -> str:
    plan = state.get("plan_summary") or {}
    member = str((state.get("resolved_member_context") or {}).get("member") or plan.get("member_label") or "你")
    results = list(state.get("tool_execution_results") or [])
    lines = [f"我帮你整理了{member}这段时间的已记录信息："]
    blocked = False
    for result in results:
        if result.get("blocked") or result.get("status") != "completed":
            blocked = True
            continue
        summary = result.get("summary") or {}
        tool = result.get("tool")
        count = result.get("count")
        if tool == "health_data.blood_pressure.summary":
            latest_s, latest_d = summary.get("latest_systolic"), summary.get("latest_diastolic")
            if latest_s is not None and latest_d is not None:
                lines.append(f"- 血压：记录 {count or 0} 次，最近一次为 {latest_s}/{latest_d} mmHg。")
            else:
                lines.append("- 血压：系统内暂无这段时间的相关记录。")
        elif tool == "health_data.metric.summary":
            value, unit = summary.get("latest_value"), summary.get("unit") or ""
            metric = _metric_label(str(summary.get("metric_type") or plan.get("metric_type") or "健康指标"))
            lines.append(f"- {metric}：记录 {count or 0} 条" + (f"，最近一次为 {value} {unit}。" if value is not None else "。"))
        elif tool == "health_data.metrics.recent":
            lines.append(f"- 健康指标：已整理 {count or 0} 条已记录指标。")
        elif tool == "health_record.symptoms.query":
            lines.append(f"- 症状记录：已保存 {count or 0} 条。")
    if blocked:
        lines.append("- 部分信息因权限设置或当前数据状态暂不可用。")
    lines.append("这些内容只整理系统内已有记录，不替代医生判断。")
    lines.append("如果需要，我也可以继续帮你查看最近一个月的记录变化。")
    return "\n".join(lines)


def _interpret_latest_tool_fact(messages: list[BaseMessage]) -> str:
    payload = _latest_tool_payload(messages) or {}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    systolic, diastolic = summary.get("latest_systolic"), summary.get("latest_diastolic")
    if isinstance(systolic, (int, float)) and isinstance(diastolic, (int, float)):
        return (
            f"你刚才查看的最近一次血压记录是 {systolic}/{diastolic} mmHg。"
            "从单次记录看，可与常见成人静息血压参考范围对照；单次测量不能代表长期情况。"
            "我可以继续帮你查看最近 7 天或 30 天的记录变化。"
        )
    return "我可以继续根据刚才已整理的系统记录说明数据变化；如果要看最新数据或换一个时间范围，我会重新查询并核对权限。"


def _trim_messages(messages: list[BaseMessage], max_messages: int) -> list[RemoveMessage]:
    maximum_total = max(6, max_messages)
    if len(messages) <= maximum_total - 1:
        return []
    systems = [message for message in messages if isinstance(message, SystemMessage)]
    capacity = max(1, maximum_total - 1 - len(systems))
    groups = _conversation_turn_groups([message for message in messages if not isinstance(message, SystemMessage)])
    kept: list[list[BaseMessage]] = []
    used = 0
    for group in reversed(groups):
        if kept and used + len(group) > capacity:
            break
        kept.append(group); used += len(group)
    keep_ids = {message.id for message in [*systems, *[item for group in reversed(kept) for item in group]]}
    return [RemoveMessage(id=message.id) for message in messages if message.id not in keep_ids]


def _conversation_turn_groups(messages: list[BaseMessage]) -> list[list[BaseMessage]]:
    groups: list[list[BaseMessage]] = []
    current: list[BaseMessage] = []
    for message in messages:
        if isinstance(message, HumanMessage) and current:
            groups.append(current); current = [message]
        else:
            current.append(message)
    if current:
        groups.append(current)
    return groups


def _messages_after_trim(messages: list[BaseMessage], removals: list[RemoveMessage]) -> list[BaseMessage]:
    removed = {item.id for item in removals}
    return [message for message in messages if message.id not in removed]


def _to_llm_messages(messages: list[BaseMessage]) -> list[LLMMessage]:
    output: list[LLMMessage] = []
    for message in messages:
        if isinstance(message, SystemMessage): output.append(LLMMessage(role="system", content=str(message.content)))
        elif isinstance(message, HumanMessage): output.append(LLMMessage(role="user", content=str(message.content)))
        elif isinstance(message, AIMessage) and not message.tool_calls: output.append(LLMMessage(role="assistant", content=str(message.content)))
    return output


def _latest_ai_content(messages: tuple[BaseMessage, ...]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and not message.tool_calls:
            return str(message.content)
    return ""


def _latest_human_content(messages: list[BaseMessage] | tuple[BaseMessage, ...]) -> str:
    return next((str(message.content).strip() for message in reversed(messages) if isinstance(message, HumanMessage)), "")


def _latest_tool_payload(messages: list[BaseMessage] | tuple[BaseMessage, ...]) -> dict[str, Any] | None:
    for message in reversed(messages):
        if isinstance(message, ToolMessage):
            try:
                payload = json.loads(str(message.content))
            except (TypeError, ValueError):
                return None
            return payload if isinstance(payload, dict) else None
    return None


def _safe_request_id(value: str | None) -> str | None:
    normalized = re.sub(r"[^A-Za-z0-9_.:-]", "", str(value or ""))[:100]
    return normalized or None


def _may_be_record_query(message: str) -> bool:
    text = message.lower()
    health_words = ("血压", "睡眠", "步数", "体重", "心率", "症状", "提醒", "文档", "报告", "健康情况", "最近怎么样", "bmi")
    query_words = ("查询", "查看", "多少", "怎么样", "最近", "记录", "爸爸", "妈妈", "我", "呢", "除了", "不只是")
    return any(word in text for word in health_words) and any(word in text for word in query_words)


def _is_health_follow_up(text: str) -> bool:
    return any(term in text for term in _HEALTH_FOLLOW_UP_TERMS)


def _requests_fresh_data(text: str) -> bool:
    return any(term in text for term in _FRESH_DATA_TERMS)


def _metric_label(metric: str) -> str:
    return {"sleep_duration": "睡眠", "steps": "步数", "weight": "体重", "heart_rate": "心率", "bmi": "BMI"}.get(metric, "健康指标")


def _local_reply(messages: list[BaseMessage], name: str) -> str:
    latest = _latest_human_content(messages)
    lowered = latest.lower()
    greeting_name = f"，{name}" if name else ""
    if any(token in lowered for token in ("你好", "您好", "hello", " hi", "hey")):
        return f"你好呀{greeting_name}。今天过得怎么样？想聊聊天，或整理一下健康记录，我都在。"
    if "我是谁" in latest:
        return f"你是{name or '当前会话的用户'}。我会在这段对话里记住我们刚才聊过的内容。"
    if "你还记得" in latest or "刚才" in latest:
        return "记得，我们还在同一段对话里。你可以接着刚才的话题继续说。"
    if "天气" in latest:
        return "我目前不能查询实时天气。不过我可以陪你聊聊，也可以在权限允许的范围内整理自己和家人的健康记录。"
    return "我在。你可以和我聊聊近况，也可以问我已记录的睡眠、血压、提醒、资料或家庭健康信息。"
