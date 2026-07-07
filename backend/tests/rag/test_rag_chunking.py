from __future__ import annotations

import unittest
import uuid

from app.rag.chunking import chunk_record
from app.rag.schemas import RagIndexRecord, RagSourceType


class RagChunkingTestCase(unittest.TestCase):
    def test_chunk_record_preserves_safe_citation_and_permission(self) -> None:
        source_id = uuid.uuid4()
        user_id = uuid.uuid4()
        record = RagIndexRecord(
            record_id=f"blood_pressure_summary:{source_id}",
            source_type=RagSourceType.BLOOD_PRESSURE_SUMMARY,
            source_id=source_id,
            owner_user_id=user_id,
            target_user_id=user_id,
            family_id=None,
            title="Blood pressure record",
            summary_text="Blood pressure values recorded for system summary only.",
            safe_excerpt="Blood pressure values recorded for system summary only.",
            permission_type="metrics",
        )

        chunks = chunk_record(record, max_chars=30)

        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0].citation, f"blood_pressure_summary:{source_id}")
        self.assertEqual(chunks[0].permission_type, "metrics")
        self.assertNotIn("file_path", chunks[0].safe_excerpt)


if __name__ == "__main__":
    unittest.main()
