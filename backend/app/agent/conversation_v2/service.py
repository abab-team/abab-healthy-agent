"""Phase B message-native conversation service backed by LangGraph state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from uuid import UUID

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import RemoveMessage

from app.agent.conversation_v2.checkpointer import PersistentConversationCheckpointer, get_persistent_checkpointer
from app.agent.conversation_v2.message_safety import sanitize_checkpoint_message
from app.agent.conversation_v2.state import ConversationState
from app.core.config import Settings, get_settings
from app.llm.client import LLMClient, get_llm_client
from app.llm.schemas import LLMMessage


SYSTEM_PROMPT = (
    "You are a friendly family health assistant. Hold a natural conversation, "
    "but do not claim to access health records or invoke tools. Keep replies concise."
)


@dataclass(frozen=True)
class ConversationTurnResult:
    thread_id: str
    answer: str
    messages: tuple[BaseMessage, ...]


class ConversationAccessDeniedError(PermissionError):
    """Raised before a checkpoint can be read for a different user."""


class ConversationRuntimeV2:
    """A pure chat graph using LangGraph's official persistent checkpointer.

    This runtime has no ToolExecutor, service, repository, or database access.
    The caller supplies the already-authorized session owner resolver; the graph
    only persists standard HumanMessage and AIMessage values under thread_id.
    """

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        checkpointer: PersistentConversationCheckpointer | None = None,
        owner_resolver: Callable[[str], UUID | None] | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.checkpointer = checkpointer or get_persistent_checkpointer(
            self.settings.CONVERSATION_RUNTIME_V2_CHECKPOINT_PATH
        )
        self.owner_resolver = owner_resolver
        self.llm_client = llm_client or get_llm_client(self.settings)
        self.graph = self._build_graph()

    def run_turn(self, *, session_id: UUID | str, user_id: UUID, user_message: str) -> ConversationTurnResult:
        thread_id = str(session_id)
        self._assert_session_owner(thread_id, user_id)
        safe_message = sanitize_checkpoint_message(user_message)
        if not safe_message:
            safe_message = "[empty message]"
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = self.graph.get_state(config)
        new_messages: list[BaseMessage] = []
        if not snapshot.values.get("messages"):
            new_messages.append(SystemMessage(content=SYSTEM_PROMPT))
        new_messages.append(HumanMessage(content=safe_message))
        state = self.graph.invoke({"messages": new_messages}, config=config)
        messages = tuple(state.get("messages", ()))
        answer = _latest_ai_content(messages)
        return ConversationTurnResult(thread_id=thread_id, answer=answer, messages=messages)

    def get_messages(self, *, session_id: UUID | str, user_id: UUID) -> tuple[BaseMessage, ...]:
        thread_id = str(session_id)
        self._assert_session_owner(thread_id, user_id)
        snapshot = self.graph.get_state({"configurable": {"thread_id": thread_id}})
        return tuple(snapshot.values.get("messages", ()))

    def close(self) -> None:
        self.checkpointer.close()

    def _assert_session_owner(self, thread_id: str, user_id: UUID) -> None:
        if self.owner_resolver is None:
            return
        owner_id = self.owner_resolver(thread_id)
        if owner_id != user_id:
            raise ConversationAccessDeniedError("conversation session is not available")

    def _build_graph(self):
        graph = StateGraph(ConversationState)
        graph.add_node("respond", self._respond)
        graph.add_edge(START, "respond")
        graph.add_edge("respond", END)
        return graph.compile(checkpointer=self.checkpointer.saver)

    def _respond(self, state: ConversationState) -> dict[str, list[BaseMessage]]:
        messages = list(state.get("messages", ()))
        removals = _trim_messages(messages, self.settings.CONVERSATION_RUNTIME_V2_MAX_MESSAGES)
        visible_messages = _messages_after_trim(messages, removals)
        answer = self._generate_reply(visible_messages)
        return {"messages": [*removals, AIMessage(content=sanitize_checkpoint_message(answer))]}

    def _generate_reply(self, messages: list[BaseMessage]) -> str:
        if self.settings.LLM_ENABLED and self.settings.LLM_CHAT_ENABLED:
            llm_messages: list[LLMMessage] = []
            for message in messages:
                if isinstance(message, SystemMessage):
                    llm_messages.append(LLMMessage(role="system", content=str(message.content)))
                elif isinstance(message, HumanMessage):
                    llm_messages.append(LLMMessage(role="user", content=str(message.content)))
                elif isinstance(message, AIMessage):
                    llm_messages.append(LLMMessage(role="assistant", content=str(message.content)))
            try:
                response = self.llm_client.chat(llm_messages, metadata={"conversation_runtime": "v2"})
                content = sanitize_checkpoint_message(response.content)
                if content:
                    return content
            except Exception:
                pass
        return _local_reply(messages)


def _trim_messages(messages: list[BaseMessage], max_messages: int) -> list[RemoveMessage]:
    # Reserve one slot for the AI response this node will append. Retain the
    # persisted system message and the newest real conversational turns.
    maximum_total = max(3, max_messages)
    allowed_before_response = maximum_total - 1
    if len(messages) <= allowed_before_response:
        return []
    system_messages = [message for message in messages if isinstance(message, SystemMessage)]
    keep_regular_count = max(1, allowed_before_response - len(system_messages))
    regular_messages = [message for message in messages if not isinstance(message, SystemMessage)]
    keep_ids = {message.id for message in system_messages + regular_messages[-keep_regular_count:]}
    return [RemoveMessage(id=message.id) for message in messages if message.id not in keep_ids]


def _messages_after_trim(messages: list[BaseMessage], removals: list[RemoveMessage]) -> list[BaseMessage]:
    removed_ids = {item.id for item in removals}
    return [message for message in messages if message.id not in removed_ids]


def _latest_ai_content(messages: tuple[BaseMessage, ...]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return str(message.content)
    return ""


def _local_reply(messages: list[BaseMessage]) -> str:
    latest = next((str(message.content).strip() for message in reversed(messages) if isinstance(message, HumanMessage)), "")
    lowered = latest.lower()
    if any(token in lowered for token in ("hello", "hi", "\u4f60\u597d", "\u60a8\u597d")):
        return "\u4f60\u597d\u5440\uff0c\u6211\u5728\u3002\u4eca\u5929\u60f3\u804a\u70b9\u4ec0\u4e48\uff1f"
    if "\u8c22" in latest or "thanks" in lowered:
        return "\u4e0d\u5ba2\u6c14\uff0c\u6211\u4f1a\u7ee7\u7eed\u8bb0\u4f4f\u8fd9\u6bb5\u5bf9\u8bdd\u3002"
    return "\u6211\u6536\u5230\u4f60\u7684\u6d88\u606f\u4e86\u3002\u4f60\u53ef\u4ee5\u7ee7\u7eed\u8bf4\u8bf4\uff0c\u6211\u4f1a\u7ed3\u5408\u8fd9\u6bb5\u5bf9\u8bdd\u63a5\u7740\u804a\u3002"
