from __future__ import annotations

import unittest
import uuid

from app.rag.schemas import RagIndexRecord, RagSourceType
from app.rag.source_policy import coerce_source_types, contains_forbidden_marker, safe_metadata, safe_text, validate_index_record


class RagSourcePolicyTestCase(unittest.TestCase):
    def test_allowed_source_types_can_be_coerced(self) -> None:
        source_types = coerce_source_types(["blood_pressure_summary", "alert_summary", "alert_summary"])

        self.assertEqual([item.value for item in source_types], ["blood_pressure_summary", "alert_summary"])

    def test_unknown_source_type_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            coerce_source_types(["external_medical_article"])

    def test_sensitive_markers_are_detected(self) -> None:
        self.assertTrue(contains_forbidden_marker("file_path=C:\\Users\\secret.pdf"))
        self.assertTrue(contains_forbidden_marker("raw_extracted_text should not be indexed"))
        self.assertFalse(contains_forbidden_marker("system record summary"))

    def test_safe_text_redacts_sensitive_content(self) -> None:
        self.assertEqual(safe_text("token=abc123"), "[redacted]")
        self.assertEqual(safe_text("  system   record  "), "system record")

    def test_safe_metadata_drops_sensitive_keys(self) -> None:
        result = safe_metadata({"title": "demo", "file_path": "storage://hidden", "count": 2})

        self.assertEqual(result["title"], "demo")
        self.assertEqual(result["count"], 2)
        self.assertNotIn("file_path", result)

    def test_validate_index_record_rejects_unsafe_excerpt(self) -> None:
        record = RagIndexRecord(
            record_id="x",
            source_type=RagSourceType.MEDICAL_DOCUMENT_METADATA,
            source_id=uuid.uuid4(),
            owner_user_id=uuid.uuid4(),
            target_user_id=uuid.uuid4(),
            family_id=None,
            title="Document",
            summary_text="file_path=/home/secret.pdf",
            safe_excerpt="file_path=/home/secret.pdf",
            permission_type="documents",
        )

        with self.assertRaises(ValueError):
            validate_index_record(record)


if __name__ == "__main__":
    unittest.main()
