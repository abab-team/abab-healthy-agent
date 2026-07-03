from __future__ import annotations

import unittest
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.modules.document_center import repository as document_repository
from app.modules.document_center import service as document_service
from app.modules.document_center.enums import DocumentExtractStatus, DocumentType
from app.modules.document_center.models import DocumentVersion
from app.modules.identity import service as identity_service


class DocumentCenterServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = SessionLocal()
        suffix = uuid4().hex[:8]
        self.user = identity_service.create_user(
            self.db,
            email=f"phase04c.document.{suffix}@example.com",
            phone=f"p04c_doc_{suffix}",
            nickname="Document User",
        )

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()

    def _create_document(self):
        return document_service.create_document_metadata(
            self.db,
            user_id=self.user.id,
            uploaded_by_user_id=self.user.id,
            document_type=DocumentType.CHECKUP_REPORT,
            title="体检报告",
            file_name="checkup.pdf",
            file_path="storage/private/checkup.pdf",
        )

    def test_create_document_metadata_success(self) -> None:
        document = self._create_document()

        self.assertEqual(document.title, "体检报告")
        self.assertEqual(document.file_path, "storage/private/checkup.pdf")

    def test_safe_summary_does_not_return_file_path(self) -> None:
        document = self._create_document()

        summary = document_service.get_document_safe_summary(self.db, document.id)

        self.assertFalse(hasattr(summary, "file_path"))
        self.assertEqual(summary.file_name, "checkup.pdf")

    def test_mark_document_extract_success_updates_status(self) -> None:
        document = self._create_document()

        updated = document_service.mark_document_extract_success(
            self.db,
            document.id,
            ai_summary="用户确认前的提取摘要",
            extracted_json={"items": []},
        )

        self.assertEqual(updated.ai_extract_status, DocumentExtractStatus.SUCCESS)
        self.assertEqual(updated.extracted_json, {"items": []})

    def test_add_document_version_success(self) -> None:
        document = self._create_document()

        version = document_service.add_document_version(
            self.db,
            document.id,
            file_name="checkup-v1.pdf",
            file_path="storage/private/checkup-v1.pdf",
        )

        self.assertEqual(version.version_no, 1)

    def test_document_version_number_is_unique_per_document(self) -> None:
        document = self._create_document()
        document_service.add_document_version(
            self.db,
            document.id,
            file_name="checkup-v1.pdf",
            file_path="storage/private/checkup-v1.pdf",
        )

        with self.assertRaises(IntegrityError):
            document_repository.create_document_version(
                self.db,
                document_id=document.id,
                version_no=1,
                file_name="duplicate.pdf",
                file_path="storage/private/duplicate.pdf",
                created_by_user_id=self.user.id,
            )

        self.db.rollback()
        count = self.db.scalar(
            select(func.count())
            .select_from(DocumentVersion)
            .where(DocumentVersion.document_id == document.id),
        )
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
