"""LangGraph state definitions for the persistent conversation runtime."""

from typing import Annotated, NotRequired, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ConversationState(TypedDict):
    """Only standard messages and non-sensitive runtime metadata enter the graph."""

    messages: Annotated[list[BaseMessage], add_messages]
    runtime_metadata: NotRequired[dict[str, str | int | bool]]
    processed_request_ids: NotRequired[list[str]]
