"""Provider contract for text generation backends."""

from abc import ABC, abstractmethod

from app.llm.schemas import LLMRequest, LLMResponse


class LLMProvider(ABC):
    """Base provider interface.

    Providers must only generate text. They must not access databases, call
    Agent tools, or make business decisions.
    """

    name: str

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate text for a normalized LLM request."""
