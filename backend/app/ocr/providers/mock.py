from __future__ import annotations

import hashlib

from app.ocr.schemas import OCRRequest, OCRResult


class MockOCRProvider:
    provider_name = "mock"

    def extract_text(self, request: OCRRequest) -> OCRResult:
        seed = f"{request.document_id}:{request.storage_key}:{request.file_name}:{request.mime_type}"
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        preview = (
            "系统内模拟 OCR 预览：已识别到一份健康资料，可用于生成待确认健康事件草稿。"
            "本阶段不进行诊断判断，不生成处方或剂量建议。"
        )
        return OCRResult(
            text_preview=preview,
            text_hash=digest,
            confidence=0.82,
            page_count=1,
            provider=self.provider_name,
            is_mock=True,
            warnings=["mock_ocr_only", "preview_not_full_text"],
            structured_hints={
                "suggested_event_type": "other",
                "suggested_title": "健康资料记录草稿",
                "text_hash": digest,
            },
        )
