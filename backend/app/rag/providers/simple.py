from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable

from app.rag.schemas import RagChunk, RagRetrievedSource


TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


class SimpleRagRetriever:
    def search(
        self,
        query: str,
        chunks: Iterable[RagChunk],
        *,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> tuple[RagRetrievedSource, ...]:
        query_tokens = _tokens(query)
        scored: list[tuple[float, RagChunk]] = []
        for chunk in chunks:
            score = _score(query_tokens, chunk.text)
            if score >= min_score:
                scored.append((score, chunk))
        scored.sort(
            key=lambda item: (
                item[0],
                item[1].source_created_at.isoformat() if item[1].source_created_at else "",
            ),
            reverse=True,
        )
        results: list[RagRetrievedSource] = []
        seen: set[str] = set()
        for score, chunk in scored:
            if chunk.citation in seen:
                continue
            seen.add(chunk.citation)
            results.append(
                RagRetrievedSource(
                    source_type=chunk.source_type.value,
                    source_id=str(chunk.source_id),
                    title=chunk.title,
                    safe_excerpt=chunk.safe_excerpt,
                    citation=chunk.citation,
                    score=round(float(score), 4),
                    permission_type=chunk.permission_type,
                    metadata=chunk.metadata_safe,
                )
            )
            if len(results) >= top_k:
                break
        return tuple(results)


def _tokens(text: str) -> Counter[str]:
    values = [token.lower() for token in TOKEN_RE.findall(text or "") if token.strip()]
    # Also add Chinese bigrams for short medical terms without external tokenizers.
    for raw in TOKEN_RE.findall(text or ""):
        if any("\u4e00" <= char <= "\u9fff" for char in raw):
            values.extend(raw[index : index + 2] for index in range(max(len(raw) - 1, 0)))
    return Counter(values)


def _score(query_tokens: Counter[str], text: str) -> float:
    if not query_tokens:
        return 0.0
    text_tokens = _tokens(text)
    if not text_tokens:
        return 0.0
    overlap = sum(min(count, text_tokens[token]) for token, count in query_tokens.items())
    substring_bonus = 1.0 if (text and any(token in text.lower() for token in query_tokens)) else 0.0
    return (overlap / max(sum(query_tokens.values()), 1)) + substring_bonus
