from __future__ import annotations

import os
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import Settings  # noqa: E402
from app.llm.client import LLMClient  # noqa: E402


SMOKE_SYSTEM_PROMPT = (
    "You are validating a text generation adapter. Do not provide diagnosis, "
    "prescription, dosage, or emergency instructions."
)
SMOKE_USER_PROMPT = "请用两句话说明今天的家庭健康简报仅基于系统记录整理，不替代医生。"


def _env_true(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _print_result(*, status: str, provider: str, model: str, is_mock: bool, latency_ms: int, content_length: int) -> None:
    print(f"STATUS={status}")
    print(f"PROVIDER={provider}")
    print(f"MODEL={model}")
    print(f"IS_MOCK={str(is_mock).lower()}")
    print(f"LATENCY_MS={latency_ms}")
    print(f"CONTENT_LENGTH={content_length}")


def main() -> int:
    real_smoke_enabled = _env_true("LLM_REAL_SMOKE_ENABLED")
    if real_smoke_enabled and not os.getenv("LLM_API_KEY", "").strip():
        print("STATUS=SKIPPED_REAL_PROVIDER_SMOKE")
        print("REASON=missing_llm_api_key")
        return 0
    if not real_smoke_enabled:
        settings = Settings(
            LLM_ENABLED=False,
            LLM_PROVIDER="mock",
            LLM_MODEL=os.getenv("LLM_MODEL", "mock-model") or "mock-model",
        )
    else:
        settings = Settings(
            LLM_ENABLED=True,
            LLM_PROVIDER=os.getenv("LLM_PROVIDER", "openai_compatible"),
            LLM_BASE_URL=os.getenv("LLM_BASE_URL", ""),
            LLM_API_KEY=os.getenv("LLM_API_KEY", ""),
            LLM_MODEL=os.getenv("LLM_MODEL", ""),
            LLM_TIMEOUT_SECONDS=float(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
            LLM_MAX_TOKENS=int(os.getenv("LLM_MAX_TOKENS", "256")),
            LLM_TEMPERATURE=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        )

    start = time.perf_counter()
    try:
        response = LLMClient(settings).generate_text(
            system_prompt=SMOKE_SYSTEM_PROMPT,
            user_prompt=SMOKE_USER_PROMPT,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=min(settings.LLM_MAX_TOKENS, 256),
            metadata={"smoke": "llm_provider"},
        )
    except Exception as exc:
        print("STATUS=FAILED_SAFE")
        print(f"ERROR_TYPE={exc.__class__.__name__}")
        return 1

    latency_ms = int((time.perf_counter() - start) * 1000)
    content = response.content or ""
    _print_result(
        status="OK",
        provider=response.provider,
        model=response.model,
        is_mock=response.is_mock,
        latency_ms=latency_ms,
        content_length=len(content),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
