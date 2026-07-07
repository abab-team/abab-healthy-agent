"""Unified LLM client entrypoint.

The client is intentionally not wired into Agent workflows in Phase 10.A.
Future workflow usage must route generated text through Agent Safety Policy.
"""

from app.core.config import Settings, get_settings
from app.llm.errors import LLMConfigurationError
from app.llm.providers import MockLLMProvider, OpenAICompatibleProvider
from app.llm.providers.base import LLMProvider
from app.llm.schemas import LLMMessage, LLMRequest, LLMResponse


class LLMClient:
    """Small facade over configured text generation providers."""

    def __init__(self, settings: Settings, provider: LLMProvider | None = None) -> None:
        self.settings = settings
        self.provider = provider or self._build_provider(settings)

    def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        metadata: dict | None = None,
    ) -> LLMResponse:
        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt),
            ],
            temperature=temperature if temperature is not None else self.settings.LLM_TEMPERATURE,
            max_tokens=max_tokens if max_tokens is not None else self.settings.LLM_MAX_TOKENS,
            metadata=metadata or {},
        )
        return self.provider.generate(request)

    def chat(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        metadata: dict | None = None,
    ) -> LLMResponse:
        request = LLMRequest(
            messages=messages,
            temperature=temperature if temperature is not None else self.settings.LLM_TEMPERATURE,
            max_tokens=max_tokens if max_tokens is not None else self.settings.LLM_MAX_TOKENS,
            metadata=metadata or {},
        )
        return self.provider.generate(request)

    @staticmethod
    def _build_provider(settings: Settings) -> LLMProvider:
        provider_name = settings.LLM_PROVIDER.strip().lower()
        if not settings.LLM_ENABLED:
            return MockLLMProvider(model=settings.LLM_MODEL)
        if provider_name == "mock":
            return MockLLMProvider(model=settings.LLM_MODEL)
        if provider_name == "openai_compatible":
            return OpenAICompatibleProvider(
                base_url=settings.LLM_BASE_URL,
                api_key=settings.LLM_API_KEY,
                model=settings.LLM_MODEL,
                timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
            )
        raise LLMConfigurationError(f"Unsupported LLM provider: {provider_name}")


def get_llm_client(settings: Settings | None = None) -> LLMClient:
    return LLMClient(settings or get_settings())
