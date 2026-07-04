from __future__ import annotations

import re
import unicodedata
from typing import Any


ALLOWED_FILE_PATH_SCHEMES = ("demo://", "storage://", "minio://", "s3://", "oss://", "cos://")
SENSITIVE_INPUT_NAMES = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "session_token",
    "session_token_hash",
    "token_hash",
    "secret",
    "api_key",
    "private_key",
}
SENSITIVE_FILE_PATH_MARKERS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "session_token",
    "session_token_hash",
    "token_hash",
    "api_key",
    "private_key",
}


def sanitize_optional_text(value: Any, *, max_length: int) -> str | None:
    if value is None:
        return None
    text = _coerce_string(value)
    text = _strip_and_reject_control_chars(text)
    if text == "":
        return None
    _reject_too_long(text, max_length)
    return text


def sanitize_required_text(value: Any, *, max_length: int) -> str:
    text = _coerce_string(value)
    text = _strip_and_reject_control_chars(text)
    if text == "":
        raise ValueError("This field is required.")
    _reject_too_long(text, max_length)
    return text


def sanitize_optional_json(value: Any, *, max_string_length: int = 1000, max_total_length: int = 10000) -> Any:
    if value is None:
        return None
    sanitized = _sanitize_json_value(value, max_string_length=max_string_length)
    _reject_too_long(repr(sanitized), max_total_length)
    return sanitized


def sanitize_required_json(value: Any, *, max_string_length: int = 1000, max_total_length: int = 10000) -> Any:
    if value is None:
        raise ValueError("This field is required.")
    sanitized = sanitize_optional_json(value, max_string_length=max_string_length, max_total_length=max_total_length)
    if sanitized is None:
        raise ValueError("This field is required.")
    return sanitized


def sanitize_file_path(value: Any, *, max_length: int = 512) -> str:
    path = sanitize_required_text(value, max_length=max_length)
    lowered = path.lower()
    if lowered.startswith("file://"):
        raise ValueError("File path is not allowed.")
    if re.match(r"^[a-zA-Z]:[\\/]", path):
        raise ValueError("File path is not allowed.")
    if path.startswith(("/", "\\")):
        raise ValueError("File path is not allowed.")
    if _has_parent_path_segment(path):
        raise ValueError("File path is not allowed.")
    if _contains_file_path_secret(lowered):
        raise ValueError("File path is not allowed.")
    if path.startswith(ALLOWED_FILE_PATH_SCHEMES):
        return path
    if "://" in path:
        raise ValueError("File path is not allowed.")
    return path


def _sanitize_json_value(value: Any, *, max_string_length: int) -> Any:
    if isinstance(value, str):
        return sanitize_required_text(value, max_length=max_string_length)
    if isinstance(value, list):
        return [_sanitize_json_value(item, max_string_length=max_string_length) for item in value]
    if isinstance(value, dict):
        sanitized: dict[Any, Any] = {}
        for key, item in value.items():
            if isinstance(key, str) and _contains_sensitive_name(key.lower()):
                raise ValueError("Sensitive field is not allowed.")
            sanitized[key] = _sanitize_json_value(item, max_string_length=max_string_length)
        return sanitized
    return value


def _coerce_string(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("Value must be a string.")
    return value


def _strip_and_reject_control_chars(text: str) -> str:
    stripped = text.strip()
    for char in stripped:
        if unicodedata.category(char) == "Cc" and char not in {"\n", "\r", "\t"}:
            raise ValueError("Control characters are not allowed.")
    return stripped


def _reject_too_long(text: str, max_length: int) -> None:
    if len(text) > max_length:
        raise ValueError(f"Value must be at most {max_length} characters.")


def _contains_sensitive_name(value: str) -> bool:
    return any(name in value for name in SENSITIVE_INPUT_NAMES)


def _contains_file_path_secret(value: str) -> bool:
    return any(name in value for name in SENSITIVE_FILE_PATH_MARKERS)


def _has_parent_path_segment(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(part == ".." for part in normalized.split("/"))
