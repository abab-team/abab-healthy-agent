"""Bounded, redacted text suitable for checkpoint persistence."""

from __future__ import annotations

import re


MAX_CHECKPOINT_MESSAGE_CHARS = 1600
_SECRET_PATTERNS = (
    re.compile(r"\b(?:api[_-]?key|token|password|secret)\s*[:=]\s*[^\s,;]+", re.IGNORECASE),
    re.compile(r"(?:\u5bc6\u7801|\u53e3\u4ee4|\u4ee4\u724c|\u5bc6\u94a5)\s*(?:\u662f|\u4e3a|[:=])\s*[^\s,;\uff0c\uff1b]+", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{8,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"traceback(?:.|\n)*", re.IGNORECASE),
    re.compile(r"\b(?:select|insert|update|delete)\s+[^\n]{1,800}", re.IGNORECASE),
)
_WINDOWS_PATH = re.compile(r"\b[A-Za-z]:\\[^\s]+")
_UNIX_PATH = re.compile(r"(?<!\w)/(?:[^\s/]+/){1,}[^\s]+")
_NATIONAL_ID = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")


def sanitize_checkpoint_message(value: object, *, max_chars: int = MAX_CHECKPOINT_MESSAGE_CHARS) -> str:
    """Return a bounded text value without secrets or machine paths.

    The checkpoint is conversation state, never a raw OCR/document store. The
    bounded value also prevents a long pasted document from becoming history.
    """

    text = str(value or "").strip()
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[redacted]", text)
    text = _NATIONAL_ID.sub("[id redacted]", text)
    text = _WINDOWS_PATH.sub("[path redacted]", text)
    text = _UNIX_PATH.sub("[path redacted]", text)
    if len(text) > max_chars:
        text = f"{text[:max_chars]}\n[long content omitted]"
    return text
