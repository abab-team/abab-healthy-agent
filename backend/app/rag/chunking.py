from __future__ import annotations

from collections.abc import Iterable

from app.rag.schemas import RagChunk, RagIndexRecord
from app.rag.source_policy import safe_text, validate_index_record


def chunk_record(record: RagIndexRecord, *, max_chars: int = 1200) -> tuple[RagChunk, ...]:
    validate_index_record(record)
    text = safe_text(record.summary_text or record.safe_excerpt, max_length=max_chars * 4)
    if not text:
        return ()
    chunks: list[RagChunk] = []
    start = 0
    index = 0
    while start < len(text):
        part = text[start : start + max_chars].strip()
        if part:
            chunks.append(
                RagChunk(
                    chunk_id=f"{record.record_id}:{index}",
                    record_id=record.record_id,
                    source_type=record.source_type,
                    source_id=record.source_id,
                    owner_user_id=record.owner_user_id,
                    target_user_id=record.target_user_id,
                    family_id=record.family_id,
                    title=record.title,
                    text=part,
                    safe_excerpt=safe_text(part, max_length=300),
                    citation=record.citation,
                    permission_type=record.permission_type,
                    permission_action=record.permission_action,
                    source_created_at=record.source_created_at,
                    tags=record.tags,
                    metadata_safe=record.metadata_safe,
                )
            )
        start += max_chars
        index += 1
    return tuple(chunks)


def chunk_records(records: Iterable[RagIndexRecord], *, max_chars: int = 1200) -> tuple[RagChunk, ...]:
    chunks: list[RagChunk] = []
    for record in records:
        chunks.extend(chunk_record(record, max_chars=max_chars))
    return tuple(chunks)
