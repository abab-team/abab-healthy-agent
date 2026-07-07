"""Internal RAG retrieval foundation.

The RAG layer only indexes safe summaries derived from existing services/data.
It must not expose raw document text, file paths, secrets, prompts, or LLM raw
responses, and it must never bypass family permissions.
"""

from app.rag.schemas import RagRetrievedSource, RagSearchResult, RagSourceType
from app.rag.service import search_rag_sources

__all__ = ["RagRetrievedSource", "RagSearchResult", "RagSourceType", "search_rag_sources"]
