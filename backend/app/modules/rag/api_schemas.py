from __future__ import annotations

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.api.validators import STRICT_MODEL_CONFIG, required_text
from app.rag.source_policy import ALLOWED_SOURCE_TYPES


RagQuery = Annotated[str, required_text(200), Field(min_length=1, max_length=200)]


class RagSearchRequest(BaseModel):
    model_config = STRICT_MODEL_CONFIG

    query: RagQuery
    target_user_id: UUID | None = None
    family_id: UUID | None = None
    source_types: list[str] | None = None
    top_k: int = Field(default=5, ge=1, le=10)

    @field_validator("source_types")
    @classmethod
    def validate_source_types(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        clean: list[str] = []
        for item in value:
            if item not in ALLOWED_SOURCE_TYPES:
                raise ValueError("source_type is not allowed")
            if item not in clean:
                clean.append(item)
        return clean


class RagRetrievedSourceResponse(BaseModel):
    source_type: str
    source_id: str
    title: str
    safe_excerpt: str
    citation: str
    score: float
    permission_type: str
    metadata: dict[str, str | int | float | bool | None]


class RagSearchResponse(BaseModel):
    query: str
    target_user_id: UUID
    family_id: UUID | None = None
    result_count: int
    rag_enabled: bool
    fallback_reason: str | None = None
    results: list[RagRetrievedSourceResponse]
