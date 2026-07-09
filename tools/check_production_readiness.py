from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


PLACEHOLDER_VALUES = {
    "",
    "change-me",
    "change-me-in-local-env",
    "family_health",
    "minioadmin",
    "password",
    "secret",
    "demo",
}


def load_env_file(path: Path | None) -> dict[str, str]:
    values: dict[str, str] = {}
    if path is None:
        return values
    if not path.exists():
        raise FileNotFoundError(f"env file not found: {path}")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def merged_env(file_values: dict[str, str]) -> dict[str, str]:
    merged = dict(file_values)
    for key, value in os.environ.items():
        merged.setdefault(key, value)
    return merged


def as_bool(values: dict[str, str], key: str, default: bool = False) -> bool:
    raw = values.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def is_strong_secret(value: str) -> bool:
    if value.strip().lower() in PLACEHOLDER_VALUES:
        return False
    return len(value) >= 32 and bool(re.search(r"[A-Za-z]", value)) and bool(re.search(r"\d", value))


def add(checks: list[tuple[str, bool, str]], name: str, ok: bool, message: str) -> None:
    checks.append((name, ok, message))


def run_checks(values: dict[str, str]) -> list[tuple[str, bool, str]]:
    checks: list[tuple[str, bool, str]] = []
    env = values.get("ENV") or values.get("APP_ENV") or ""
    database_url = values.get("DATABASE_URL", "")
    cors_origins = split_csv(values.get("CORS_ORIGINS") or values.get("CORS_ALLOW_ORIGINS", ""))

    add(checks, "environment", env == "production", "ENV or APP_ENV must be production.")
    add(checks, "debug", not as_bool(values, "DEBUG", default=True), "DEBUG must be false.")
    add(checks, "auth_enabled", as_bool(values, "AUTH_ENABLED"), "AUTH_ENABLED must be true.")
    add(
        checks,
        "demo_header_disabled",
        not as_bool(values, "AUTH_DEMO_HEADER_ENABLED", default=True),
        "AUTH_DEMO_HEADER_ENABLED must be false.",
    )
    add(checks, "secret_key", is_strong_secret(values.get("SECRET_KEY", "")), "SECRET_KEY must be strong and non-placeholder.")
    add(
        checks,
        "jwt_secret_key",
        is_strong_secret(values.get("JWT_SECRET_KEY", "")),
        "JWT_SECRET_KEY must be strong and non-placeholder.",
    )
    add(
        checks,
        "database_url",
        database_url.startswith(("postgresql://", "postgresql+psycopg://"))
        and "localhost" not in database_url
        and "family_health:family_health" not in database_url,
        "DATABASE_URL must point to production PostgreSQL, not local/demo credentials.",
    )
    add(
        checks,
        "cors_origins",
        bool(cors_origins)
        and "*" not in cors_origins
        and all("localhost" not in origin and "127.0.0.1" not in origin for origin in cors_origins),
        "CORS origins must be explicit production origins.",
    )
    add(
        checks,
        "raw_ocr_storage",
        not as_bool(values, "OCR_STORE_RAW_TEXT"),
        "OCR_STORE_RAW_TEXT must stay false unless separately reviewed.",
    )
    add(
        checks,
        "rag_raw_text",
        not as_bool(values, "RAG_STORE_RAW_TEXT"),
        "RAG_STORE_RAW_TEXT must stay false.",
    )
    add(
        checks,
        "external_medical_knowledge",
        not as_bool(values, "RAG_ALLOW_EXTERNAL_KNOWLEDGE"),
        "RAG_ALLOW_EXTERNAL_KNOWLEDGE must stay false without separate review.",
    )
    add(
        checks,
        "llm_api_key_not_placeholder",
        values.get("LLM_ENABLED", "false").lower() != "true"
        or values.get("LLM_PROVIDER", "mock") == "mock"
        or bool(values.get("LLM_API_KEY", "").strip()),
        "Real LLM provider requires LLM_API_KEY from environment.",
    )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Check production readiness environment settings.")
    parser.add_argument("--env-file", type=Path, default=None, help="Optional .env-style file to validate.")
    args = parser.parse_args()

    try:
        values = merged_env(load_env_file(args.env_file))
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 2

    checks = run_checks(values)
    failed = [item for item in checks if not item[1]]
    for name, ok, message in checks:
        status = "PASS" if ok else "FAIL"
        print(f"{status} {name}: {message}")
    if failed:
        print(f"production readiness failed: {len(failed)} check(s) need attention")
        return 1
    print("production readiness checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
