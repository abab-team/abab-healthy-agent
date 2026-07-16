"""OpenAI-compatible chat completions provider."""

from typing import Any

import httpx

from app.llm.errors import LLMConfigurationError, LLMProviderError, LLMTimeoutError
from app.llm.schemas import LLMRequest, LLMResponse, LLMUsage
from app.llm.providers.base import LLMProvider


def _flatten_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return ""


class OpenAICompatibleProvider(LLMProvider):
    name = "openai_compatible"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
    ) -> None:
        if not api_key:
            raise LLMConfigurationError("LLM API key is required for openai_compatible provider.")
        if not base_url:
            raise LLMConfigurationError("LLM base_url is required for openai_compatible provider.")
        if not model:
            raise LLMConfigurationError("LLM model is required for openai_compatible provider.")

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, request: LLMRequest) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in request.messages
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        payload = {key: value for key, value in payload.items() if value is not None}

        try:
            # Provider calls must not inherit HTTP_PROXY/HTTPS_PROXY from a
            # developer shell. Domain-specific routing remains the operating
            # system's responsibility, while this avoids accidental app-level
            # forwarding through a configured environment proxy.
            with httpx.Client(timeout=self.timeout_seconds, trust_env=False) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError("LLM provider request timed out.") from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError("LLM provider request failed.") from exc

        data = response.json()
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LLMProviderError("LLM provider response did not include choices.")

        first = choices[0]
        if not isinstance(first, dict):
            raise LLMProviderError("LLM provider response choice was invalid.")
        message = first.get("message")
        if not isinstance(message, dict):
            raise LLMProviderError("LLM provider response message was invalid.")

        content = _flatten_content(message.get("content"))
        usage_data = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        return LLMResponse(
            content=content,
            provider=self.name,
            model=self.model,
            is_mock=False,
            usage=LLMUsage(
                prompt_tokens=usage_data.get("prompt_tokens"),
                completion_tokens=usage_data.get("completion_tokens"),
                total_tokens=usage_data.get("total_tokens"),
            ),
            finish_reason=first.get("finish_reason"),
        )
