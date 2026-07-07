from __future__ import annotations

from typing import Protocol

from app.ocr.schemas import OCRRequest, OCRResult


class OCRProvider(Protocol):
    provider_name: str

    def extract_text(self, request: OCRRequest) -> OCRResult:
        ...
