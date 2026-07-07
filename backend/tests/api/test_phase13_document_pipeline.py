from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from uuid import UUID

TEST_DB_PATH = Path(tempfile.gettempdir()) / "family_health_agent_phase13_api.sqlite3"
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{TEST_DB_PATH.as_posix()}"
os.environ.setdefault("JWT_SECRET_KEY", "api-test-jwt-secret")
os.environ.setdefault("AUTH_DEMO_HEADER_ENABLED", "true")

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.modules.document_center.models import MedicalDocument
from app.modules.document_processing.models import DocumentExtractionResult, MedicalEventDraft
from app.modules.medical_timeline.models import MedicalEvent
from tests.api.helpers import auth_headers, client, create_user, reset_database


class TestPhase13DocumentPipeline(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        os.environ["OCR_ENABLED"] = "false"
        get_settings.cache_clear()
        self.user = create_user("phase13")
        self.headers = auth_headers(self.user["id"])

    def tearDown(self) -> None:
        os.environ["OCR_ENABLED"] = "false"
        get_settings.cache_clear()

    def test_upload_rejects_missing_auth(self) -> None:
        response = client.post(
            "/api/v1/documents/me/upload",
            content=b"%PDF-1.4\n",
            headers={"Content-Type": "application/pdf", "X-File-Name": "report.pdf"},
        )
        assert response.status_code in {401, 403}

    def test_upload_rejects_unsupported_mime_and_dangerous_filename(self) -> None:
        response = client.post(
            "/api/v1/documents/me/upload",
            headers={**self.headers, "Content-Type": "text/plain", "X-File-Name": "run.ps1"},
            content=b"Write-Host bad",
        )
        assert response.status_code == 400
        assert "Write-Host" not in response.text

    def test_upload_rejects_oversize_file(self) -> None:
        response = client.post(
            "/api/v1/documents/me/upload",
            headers={**self.headers, "Content-Type": "application/pdf", "X-File-Name": "large.pdf"},
            content=b"x" * (11 * 1024 * 1024),
        )
        assert response.status_code == 400
        assert "too large" in response.text

    def test_upload_sanitizes_filename_and_hides_storage_path(self) -> None:
        response = client.post(
            "/api/v1/documents/me/upload?document_type=checkup_report&title=%E4%BD%93%E6%A3%80%E8%B5%84%E6%96%99",
            headers={**self.headers, "Content-Type": "application/pdf", "X-File-Name": "../C:/Users/secret/report.pdf"},
            content=b"%PDF-1.4\n",
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["file_name"] == "report.pdf"
        assert "file_path" not in body
        assert "C:" not in response.text
        with SessionLocal() as db:
            document = db.get(MedicalDocument, UUID(body["id"]))
            assert document is not None
            assert document.file_path.startswith("documents/")
            assert not Path(document.file_path).is_absolute()

    def test_processing_job_query_and_safe_failed_error(self) -> None:
        document_id = self._upload_document()
        created = client.post(
            f"/api/v1/document-processing/me/documents/{document_id}/jobs",
            headers=self.headers,
            json={"job_type": "ocr"},
        )
        assert created.status_code == 201, created.text
        job_id = created.json()["id"]
        detail = client.get(f"/api/v1/document-processing/me/jobs/{job_id}", headers=self.headers)
        assert detail.status_code == 200
        failed = client.post(
            f"/api/v1/document-processing/me/jobs/{job_id}/failed",
            headers=self.headers,
            json={"error_message": "Traceback SELECT * FROM secret C:\\Users\\x"},
        )
        assert failed.status_code == 200
        assert failed.json()["error_message"] == "processing failed safely"
        listed = client.get(f"/api/v1/document-processing/me/documents/{document_id}/jobs", headers=self.headers)
        assert listed.status_code == 200
        assert len(listed.json()["items"]) == 1

    def test_mock_ocr_requires_enabled_config(self) -> None:
        document_id = self._upload_document()
        job_id = self._create_job(document_id)
        response = client.post(f"/api/v1/document-processing/me/jobs/{job_id}/run-mock-ocr", headers=self.headers)
        assert response.status_code == 400
        assert "api_key" not in response.text.lower()

    def test_mock_ocr_creates_safe_extraction_result(self) -> None:
        os.environ["OCR_ENABLED"] = "true"
        get_settings.cache_clear()
        document_id = self._upload_document()
        job_id = self._create_job(document_id)
        response = client.post(f"/api/v1/document-processing/me/jobs/{job_id}/run-mock-ocr", headers=self.headers)
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["processing_job_id"] == job_id
        assert body["raw_text_excerpt"] is None
        assert body["status"] == "needs_review"
        assert "file_path" not in response.text
        assert "raw_extracted_text" not in response.text
        with SessionLocal() as db:
            assert len(list(db.scalars(select(DocumentExtractionResult)))) == 1
            assert len(list(db.scalars(select(MedicalEvent)))) == 0

    def test_ocr_result_can_create_pending_medical_event_draft_via_agent_only(self) -> None:
        os.environ["OCR_ENABLED"] = "true"
        get_settings.cache_clear()
        document_id = self._upload_document()
        job_id = self._create_job(document_id)
        extraction = client.post(f"/api/v1/document-processing/me/jobs/{job_id}/run-mock-ocr", headers=self.headers).json()
        preview_payload = self._agent_payload(document_id, extraction["id"], confirmation=False)
        preview = client.post("/api/v1/agent/runs", headers=self.headers, json=preview_payload)
        assert preview.status_code == 201, preview.text
        assert "no draft was created" in preview.json()["generated_content"]
        with SessionLocal() as db:
            assert len(list(db.scalars(select(MedicalEventDraft)))) == 0

        confirm_payload = self._agent_payload(document_id, extraction["id"], confirmation=True)
        confirmed = client.post("/api/v1/agent/runs", headers=self.headers, json=confirm_payload)
        assert confirmed.status_code == 201, confirmed.text
        body = confirmed.json()
        assert body["status"] == "completed"
        assert body["trace_id"]
        assert "formal_event_created=false" in body["generated_content"]
        assert "raw_extracted_text" not in confirmed.text
        assert "file_path" not in confirmed.text
        with SessionLocal() as db:
            drafts = list(db.scalars(select(MedicalEventDraft)))
            assert len(drafts) == 1
            assert str(drafts[0].extraction_result_id) == extraction["id"]
            assert len(list(db.scalars(select(MedicalEvent)))) == 0

    def _upload_document(self) -> str:
        response = client.post(
            "/api/v1/documents/me/upload?document_type=checkup_report&title=%E4%BD%93%E6%A3%80%E8%B5%84%E6%96%99",
            headers={**self.headers, "Content-Type": "application/pdf", "X-File-Name": "report.pdf"},
            content=b"%PDF-1.4\n",
        )
        assert response.status_code == 201, response.text
        return response.json()["id"]

    def _create_job(self, document_id: str) -> str:
        response = client.post(
            f"/api/v1/document-processing/me/documents/{document_id}/jobs",
            headers=self.headers,
            json={"job_type": "ocr"},
        )
        assert response.status_code == 201, response.text
        return response.json()["id"]

    def _agent_payload(self, document_id: str, extraction_result_id: str, *, confirmation: bool) -> dict:
        return {
            "target_user_id": self.user["id"],
            "workflow_type": "medical_event_draft_create",
            "user_message": "根据系统内 OCR 预览生成健康事件草稿，等待用户确认。",
            "confirmation": confirmation,
            "workflow_payload": {
                "source_document_id": document_id,
                "extraction_result_id": extraction_result_id,
                "draft_title": "健康资料记录草稿",
                "extracted_text_preview": "系统内 OCR 预览，可用于整理待确认健康事件草稿。",
                "structured_hints": {"suggested_event_type": "other"},
            },
        }
