from __future__ import annotations


class OCRError(RuntimeError):
    pass


class OCRConfigurationError(OCRError):
    pass


class OCRProviderError(OCRError):
    pass
