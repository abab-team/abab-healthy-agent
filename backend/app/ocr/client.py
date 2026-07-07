from __future__ import annotations

from app.core.config import Settings
from app.ocr.errors import OCRConfigurationError
from app.ocr.providers.mock import MockOCRProvider
from app.ocr.schemas import OCRRequest, OCRResult


class OCRClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider = _provider(settings)

    def extract_text(self, request: OCRRequest) -> OCRResult:
        if not self.settings.OCR_ENABLED:
            raise OCRConfigurationError("ocr is disabled")
        return self.provider.extract_text(request)


def get_ocr_client(settings: Settings) -> OCRClient:
    return OCRClient(settings)


def _provider(settings: Settings):
    if settings.OCR_PROVIDER == "mock":
        return MockOCRProvider()
    raise OCRConfigurationError("unsupported ocr provider")
