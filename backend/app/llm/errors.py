"""LLM error types with sanitized messages."""


class LLMError(Exception):
    """Base error for the LLM adapter layer."""


class LLMConfigurationError(LLMError):
    """Raised when LLM configuration is missing or invalid."""


class LLMProviderError(LLMError):
    """Raised when an upstream provider returns an unusable response."""


class LLMTimeoutError(LLMProviderError):
    """Raised when an upstream provider request times out."""

