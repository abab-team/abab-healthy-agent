"""Schemas for the LLM adapter layer."""

from dataclasses import dataclass, field
from typing import Any, Literal


LLMRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class LLMMessage:
    role: LLMRole
    content: str


@dataclass(frozen=True)
class LLMUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class LLMRequest:
    messages: list[LLMMessage]
    temperature: float | None = None
    max_tokens: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMResponse:
    content: str
    provider: str
    model: str
    is_mock: bool
    usage: LLMUsage | None = None
    finish_reason: str | None = None
    error: str | None = None

