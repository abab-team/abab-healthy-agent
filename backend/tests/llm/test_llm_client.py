import unittest
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import Settings  # noqa: E402
from app.llm.client import get_llm_client  # noqa: E402
from app.llm.errors import LLMConfigurationError  # noqa: E402
from app.llm.schemas import LLMMessage, LLMResponse  # noqa: E402


class LLMClientTests(unittest.TestCase):
    def test_default_configuration_uses_mock_provider(self) -> None:
        client = get_llm_client(Settings(LLM_ENABLED=False, LLM_PROVIDER="mock", LLM_MODEL="mock-model"))

        response = client.generate_text(system_prompt="system", user_prompt="hello")

        self.assertIsInstance(response, LLMResponse)
        self.assertEqual(response.provider, "mock")
        self.assertTrue(response.is_mock)
        self.assertIn("Mock LLM response", response.content)

    def test_mock_provider_returns_stable_text(self) -> None:
        client = get_llm_client(Settings(LLM_PROVIDER="mock", LLM_ENABLED=True))

        first = client.generate_text(system_prompt="system", user_prompt="hello")
        second = client.generate_text(system_prompt="system", user_prompt="different")

        self.assertEqual(first.content, second.content)
        self.assertEqual(first.finish_reason, "mock")

    def test_disabled_llm_does_not_build_external_provider(self) -> None:
        settings = Settings(
            LLM_ENABLED=False,
            LLM_PROVIDER="openai_compatible",
            LLM_BASE_URL="https://example.invalid/v1",
            LLM_API_KEY="",
            LLM_MODEL="test-model",
        )

        response = get_llm_client(settings).generate_text(system_prompt="system", user_prompt="hello")

        self.assertEqual(response.provider, "mock")
        self.assertTrue(response.is_mock)

    def test_openai_compatible_requires_api_key(self) -> None:
        settings = Settings(
            LLM_ENABLED=True,
            LLM_PROVIDER="openai_compatible",
            LLM_BASE_URL="https://example.invalid/v1",
            LLM_API_KEY="",
            LLM_MODEL="test-model",
        )

        with self.assertRaises(LLMConfigurationError) as context:
            get_llm_client(settings)

        self.assertNotIn("secret", str(context.exception).lower())
        self.assertNotIn("api_key=", str(context.exception).lower())

    def test_unknown_provider_fails_safely(self) -> None:
        with self.assertRaises(LLMConfigurationError):
            get_llm_client(Settings(LLM_ENABLED=True, LLM_PROVIDER="unknown"))

    def test_chat_schema_output_is_valid(self) -> None:
        client = get_llm_client(Settings(LLM_ENABLED=False, LLM_PROVIDER="mock", LLM_MODEL="mock-model"))

        response = client.chat([LLMMessage(role="user", content="hello")])

        self.assertEqual(response.provider, "mock")
        self.assertEqual(response.model, "mock-model")
        self.assertIsNotNone(response.usage)
        self.assertIsNone(response.error)


if __name__ == "__main__":
    unittest.main()
