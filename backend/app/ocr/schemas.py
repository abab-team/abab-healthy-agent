from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OCRRequest:
    document_id: str
    storage_key: str
    file_name: str
    mime_type: str | None


@dataclass(frozen=True)
class OCRResult:
    text_preview: str
    text_hash: str
    language: str = "zh-CN"
    confidence: float | None = None
    page_count: int | None = None
    provider: str = "mock"
    is_mock: bool = True
    warnings: list[str] = field(default_factory=list)
    structured_hints: dict = field(default_factory=dict)
