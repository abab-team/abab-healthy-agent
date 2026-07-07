from __future__ import annotations

import unittest
import uuid

from app.rag.providers.simple import SimpleRagRetriever
from app.rag.schemas import RagChunk, RagSourceType


class RagRetrievalTestCase(unittest.TestCase):
    def test_simple_retriever_returns_relevant_safe_source(self) -> None:
        user_id = uuid.uuid4()
        source_id = uuid.uuid4()
        chunks = (
            RagChunk(
                chunk_id="a:0",
                record_id="a",
                source_type=RagSourceType.BLOOD_PRESSURE_SUMMARY,
                source_id=source_id,
                owner_user_id=user_id,
                target_user_id=user_id,
                family_id=None,
                title="Blood pressure",
                text="Blood pressure values were recorded yesterday.",
                safe_excerpt="Blood pressure values were recorded yesterday.",
                citation=f"blood_pressure_summary:{source_id}",
                permission_type="metrics",
                permission_action="view",
            ),
        )

        results = SimpleRagRetriever().search("blood pressure", chunks, top_k=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source_type, "blood_pressure_summary")
        self.assertGreater(results[0].score, 0)


if __name__ == "__main__":
    unittest.main()
