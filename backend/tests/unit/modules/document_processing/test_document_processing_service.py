from __future__ import annotations

import unittest
from uuid import uuid4

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.modules.document_center import service as document_service
from app.modules.document_center.enums import DocumentExtractStatus, DocumentType
from app.modules.document_processing import service as processing_service
from app.modules.document_processing.enums import (
    DocumentProcessingStatus,
    MedicalEventDraftStatus,
)
from app.modules.document_processing.exceptions import (
    InvalidMedicalEventDraftError,
    MedicalEventDraftNotPendingError,
)
from app.modules.medical_timeline.enums import MedicalEventType
from app.modules.medical_timeline.models import MedicalEvent
from app.modules.identity import service as identity_service


class DocumentProcessingServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = SessionLocal()
        suffix = uuid4().hex[:8]
        self.user = identity_service.create_user(
            self.db,
            email=f"phase04c.processing.{suffix}@example.com",
            phone=f"p04c_proc_{suffix}",
            nickname="Processing User",
        )
        self.document = document_service.create_document_metadata(
            self.db,
            user_id=self.user.id,
            uploaded_by_user_id=self.user.id,
            document_type=DocumentType.CHECKUP_REPORT,
            title="体检报告",
            file_name="checkup.pdf",
            file_path="storage/private/checkup.pdf",
        )

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()

    def test_processing_job_status_flow(self) -> None:
        job = processing_service.create_processing_job(
            self.db,
            document_id=self.document.id,
            user_id=self.user.id,
        )

        started = processing_service.mark_job_started(self.db, job.id)
        self.assertEqual(started.attempt_count, 1)
        self.assertEqual(started.status, DocumentProcessingStatus.PROCESSING)

        success = processing_service.mark_job_success(self.db, job.id)
        self.assertEqual(success.status, DocumentProcessingStatus.SUCCESS)

        failed = processing_service.mark_job_failed(self.db, job.id, "demo failure")

        self.assertEqual(failed.status, DocumentProcessingStatus.FAILED)

    def test_save_extraction_result_does_not_create_medical_event(self) -> None:
        processing_service.save_extraction_result(
            self.db,
            document_id=self.document.id,
            user_id=self.user.id,
            ai_summary="提取结果草稿",
        )

        event_count = self.db.scalar(
            select(func.count())
            .select_from(MedicalEvent)
            .where(MedicalEvent.user_id == self.user.id),
        )

        self.assertEqual(event_count, 0)

    def test_create_medical_event_draft_pending(self) -> None:
        draft = processing_service.create_medical_event_draft(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            draft_event_type=MedicalEventType.CHECKUP,
            draft_json={"medical_event": {"title": "体检事件"}},
        )

        self.assertEqual(draft.status, MedicalEventDraftStatus.PENDING)

    def test_confirm_medical_event_draft_creates_event_and_updates_document(self) -> None:
        draft = processing_service.create_medical_event_draft(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            source_document_id=self.document.id,
            draft_event_type=MedicalEventType.CHECKUP,
            draft_json={
                "medical_event": {
                    "event_type": "checkup",
                    "title": "体检事件",
                    "summary": "用户确认的体检摘要",
                },
            },
        )

        event = processing_service.confirm_medical_event_draft(
            self.db,
            draft_id=draft.id,
            confirmed_by_user_id=self.user.id,
        )

        self.assertEqual(event.title, "体检事件")
        self.assertIsNone(event.diagnosis_text)
        self.assertEqual(draft.status, MedicalEventDraftStatus.CONFIRMED)
        self.assertEqual(self.document.related_event_count, 1)
        self.assertEqual(self.document.ai_extract_status, DocumentExtractStatus.CONFIRMED)

    def test_confirmed_draft_cannot_confirm_twice(self) -> None:
        draft = processing_service.create_medical_event_draft(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            draft_event_type=MedicalEventType.CHECKUP,
            draft_json={"medical_event": {"title": "体检事件"}},
        )
        processing_service.confirm_medical_event_draft(
            self.db,
            draft_id=draft.id,
            confirmed_by_user_id=self.user.id,
        )

        with self.assertRaises(MedicalEventDraftNotPendingError):
            processing_service.confirm_medical_event_draft(
                self.db,
                draft_id=draft.id,
                confirmed_by_user_id=self.user.id,
            )

    def test_cancelled_draft_cannot_confirm(self) -> None:
        draft = processing_service.create_medical_event_draft(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            draft_event_type=MedicalEventType.CHECKUP,
            draft_json={"medical_event": {"title": "体检事件"}},
        )
        processing_service.cancel_medical_event_draft(self.db, draft.id)

        with self.assertRaises(MedicalEventDraftNotPendingError):
            processing_service.confirm_medical_event_draft(
                self.db,
                draft_id=draft.id,
                confirmed_by_user_id=self.user.id,
            )

    def test_invalid_draft_without_title_or_summary_is_rejected(self) -> None:
        draft = processing_service.create_medical_event_draft(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            draft_event_type=MedicalEventType.CHECKUP,
            draft_json={"medical_event": {"event_type": "checkup"}},
        )

        with self.assertRaises(InvalidMedicalEventDraftError):
            processing_service.confirm_medical_event_draft(
                self.db,
                draft_id=draft.id,
                confirmed_by_user_id=self.user.id,
            )


if __name__ == "__main__":
    unittest.main()
