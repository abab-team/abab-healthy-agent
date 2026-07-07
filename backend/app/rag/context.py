from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.rag.schemas import RagSearchResult
from app.rag.service import build_rag_citation_lines, search_rag_sources


def safe_rag_context_for_agent(
    db: Session,
    *,
    current_user_id: UUID,
    target_user_id: UUID,
    family_id: UUID | None,
    query: str,
    source_types: list[str] | None = None,
    top_k: int | None = None,
    settings: Settings | None = None,
) -> tuple[RagSearchResult | None, list[str], str | None]:
    effective_settings = settings or get_settings()
    if not effective_settings.RAG_ENABLED:
        return None, [], "rag_disabled"
    try:
        result = search_rag_sources(
            db,
            current_user_id=current_user_id,
            target_user_id=target_user_id,
            family_id=family_id,
            query=query,
            source_types=source_types,
            top_k=top_k,
            settings=effective_settings,
        )
    except Exception:
        return None, [], "rag_error"
    if result.fallback_reason:
        return result, [], result.fallback_reason
    return result, build_rag_citation_lines(result, max_items=top_k or effective_settings.RAG_TOP_K), None
