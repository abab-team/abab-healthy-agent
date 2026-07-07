from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id_for_demo, get_db
from app.api.errors import raise_bad_request, raise_permission_denied
from app.modules.rag.api_schemas import RagRetrievedSourceResponse, RagSearchRequest, RagSearchResponse
from app.rag.service import search_rag_sources


router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/search", response_model=RagSearchResponse, status_code=status.HTTP_200_OK)
def search_rag(
    payload: RagSearchRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> RagSearchResponse:
    target_user_id = payload.target_user_id or current_user_id
    if target_user_id != current_user_id and payload.family_id is None:
        raise_permission_denied("Family access requires a family_id.")
    try:
        result = search_rag_sources(
            db,
            current_user_id=current_user_id,
            target_user_id=target_user_id,
            family_id=payload.family_id,
            query=payload.query,
            source_types=payload.source_types,
            top_k=payload.top_k,
        )
    except ValueError as exc:
        raise_bad_request(str(exc))
    if result.fallback_reason == "permission_denied":
        raise_permission_denied()
    return RagSearchResponse(
        query=result.query,
        target_user_id=result.target_user_id,
        family_id=result.family_id,
        result_count=len(result.results),
        rag_enabled=result.rag_enabled,
        fallback_reason=result.fallback_reason,
        results=[
            RagRetrievedSourceResponse(
                source_type=item.source_type,
                source_id=item.source_id,
                title=item.title,
                safe_excerpt=item.safe_excerpt,
                citation=item.citation,
                score=item.score,
                permission_type=item.permission_type,
                metadata=item.metadata,
            )
            for item in result.results
        ],
    )
