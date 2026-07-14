"""LangGraph state definitions for the persistent conversation runtime."""

from typing import Annotated, Any, NotRequired, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ConversationState(TypedDict):
    """Message-native, non-sensitive state for Conversation Runtime V2.

    ``messages`` remains the source of conversational truth.  The other fields
    are short-lived execution metadata only; they never contain database rows,
    raw document/OCR text, file paths, credentials, or user-controlled ids.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    runtime_metadata: NotRequired[dict[str, str | int | bool]]
    processed_request_ids: NotRequired[list[str]]
    pending_tool_calls: NotRequired[list[dict[str, Any]]]
    validated_tool_calls: NotRequired[list[dict[str, Any]]]
    tool_execution_results: NotRequired[list[dict[str, Any]]]
    resolved_member_context: NotRequired[dict[str, str | bool | None]]
    permission_context: NotRequired[dict[str, str | bool | None]]
    plan_summary: NotRequired[dict[str, str | int | bool | None]]
