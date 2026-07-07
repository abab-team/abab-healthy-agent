"""Deterministic mock provider for tests and local development."""

from app.llm.schemas import LLMRequest, LLMResponse, LLMUsage
from app.llm.providers.base import LLMProvider


class MockLLMProvider(LLMProvider):
    name = "mock"

    def __init__(self, model: str = "mock-model") -> None:
        self.model = model

    def generate(self, request: LLMRequest) -> LLMResponse:
        del request
        return LLMResponse(
            content=(
                "Mock LLM response. This deterministic text is for local "
                "development only and has not executed a clinical workflow."
            ),
            provider=self.name,
            model=self.model,
            is_mock=True,
            usage=LLMUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            finish_reason="mock",
        )
