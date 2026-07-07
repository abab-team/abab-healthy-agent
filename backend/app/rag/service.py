from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.rag.chunking import chunk_records
from app.rag.index_builder import build_internal_rag_records
from app.rag.providers.simple import SimpleRagRetriever
from app.rag.schemas import RagSearchResult, RagSourceType
from app.rag.source_policy import (
    coerce_source_types,
    has_any_requested_permission,
    has_record_permission,
    validate_index_record,
)


def search_rag_sources(
    db: Session,
    *,
    current_user_id: UUID,
    target_user_id: UUID,
    family_id: UUID | None,
    query: str,
    source_types: list[str] | tuple[str, ...] | None = None,
    top_k: int | None = None,
    settings: Settings | None = None,
) -> RagSearchResult:
    effective_settings = settings or get_settings()
    normalized_query = " ".join(str(query or "").split())
    if not normalized_query:
        raise ValueError("query is required")
    if not effective_settings.RAG_ENABLED:
        return RagSearchResult(
            query=normalized_query,
            target_user_id=target_user_id,
            family_id=family_id,
            results=(),
            rag_enabled=False,
            fallback_reason="rag_disabled",
        )
    requested_source_types = coerce_source_types(source_types)
    if not has_any_requested_permission(
        db,
        current_user_id=current_user_id,
        target_user_id=target_user_id,
        family_id=family_id,
        source_types=requested_source_types,
    ):
        return RagSearchResult(
            query=normalized_query,
            target_user_id=target_user_id,
            family_id=family_id,
            results=(),
            rag_enabled=True,
            fallback_reason="permission_denied",
        )
    raw_records = build_internal_rag_records(
        db,
        target_user_id=target_user_id,
        family_id=family_id,
        source_types=requested_source_types,
    )
    allowed_records = tuple(
        validate_index_record(record)
        for record in raw_records
        if _record_matches_request(record, requested_source_types)
        and has_record_permission(db, current_user_id=current_user_id, record=record)
    )
    max_chunk_chars = max(100, int(effective_settings.RAG_MAX_CHUNK_CHARS))
    chunks = chunk_records(allowed_records, max_chars=max_chunk_chars)
    limit = _effective_top_k(top_k, settings=effective_settings)
    results = SimpleRagRetriever().search(
        normalized_query,
        chunks,
        top_k=limit,
        min_score=float(effective_settings.RAG_MIN_SCORE),
    )
    return RagSearchResult(
        query=normalized_query,
        target_user_id=target_user_id,
        family_id=family_id,
        results=results,
        rag_enabled=True,
    )


def build_rag_citation_lines(result: RagSearchResult, *, max_items: int = 5) -> list[str]:
    if not result.rag_enabled:
        return []
    if result.fallback_reason:
        return []
    lines = []
    for source in result.results[:max_items]:
        excerpt = source.safe_excerpt[:180]
        lines.append(f"- {source.title} ({source.citation}): {excerpt}")
    return lines


def _effective_top_k(top_k: int | None, *, settings: Settings) -> int:
    requested = top_k if top_k is not None else int(settings.RAG_TOP_K)
    return min(max(int(requested), 1), max(int(settings.RAG_TOP_K), 1), 10)


def _record_matches_request(record, requested_source_types: tuple[RagSourceType, ...]) -> bool:
    return record.source_type in requested_source_types
