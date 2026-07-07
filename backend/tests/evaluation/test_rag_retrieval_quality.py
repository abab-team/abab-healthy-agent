from __future__ import annotations

import unittest
import uuid

from app.rag.providers.simple import SimpleRagRetriever
from app.rag.schemas import RagChunk, RagSourceType


class RagRetrievalQualityTestCase(unittest.TestCase):
    def test_synthetic_retrieval_prefers_matching_internal_record(self) -> None:
        user_id = uuid.uuid4()
        bp_id = uuid.uuid4()
        alert_id = uuid.uuid4()
        chunks = (
            _chunk("bp", RagSourceType.BLOOD_PRESSURE_SUMMARY, bp_id, user_id, "Recorded blood pressure values for this week."),
            _chunk("alert", RagSourceType.ALERT_SUMMARY, alert_id, user_id, "A regular hydration reminder is active."),
        )

        results = SimpleRagRetriever().search("blood pressure", chunks, top_k=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source_id, str(bp_id))


def _chunk(record_id: str, source_type: RagSourceType, source_id, user_id, text: str) -> RagChunk:
    return RagChunk(
        chunk_id=f"{record_id}:0",
        record_id=record_id,
        source_type=source_type,
        source_id=source_id,
        owner_user_id=user_id,
        target_user_id=user_id,
        family_id=None,
        title=source_type.value,
        text=text,
        safe_excerpt=text,
        citation=f"{source_type.value}:{source_id}",
        permission_type="metrics" if source_type == RagSourceType.BLOOD_PRESSURE_SUMMARY else "alerts",
        permission_action="view",
    )


if __name__ == "__main__":
    unittest.main()
