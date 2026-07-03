from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class MemberCandidate:
    family_member_id: UUID
    target_user_id: UUID
    display_name: str | None
    relationship_label: str | None


@dataclass(frozen=True)
class MemberResolutionResult:
    success: bool
    target_user_id: UUID | None
    family_member_id: UUID | None
    display_name: str | None
    relationship_label: str | None
    confidence: float
    need_clarification: bool
    candidates: list[MemberCandidate]
    message: str
