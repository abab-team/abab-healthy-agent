from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolResultSummary:
    tool_name: str
    status: str
    blocked: bool = False
    count: int | None = None
    coverage_note: str | None = None


@dataclass(frozen=True)
class CriticReviewRequest:
    workflow_type: str
    user_question_excerpt: str
    draft_answer: str
    safe_tool_result_summary: str
    tool_result_summaries: tuple[ToolResultSummary, ...] = ()
    plan_intent: str | None = None
    time_range_label: str | None = None


@dataclass(frozen=True)
class CriticReviewResult:
    passed: bool
    risk_flags: list[str] = field(default_factory=list)
    grounding_flags: list[str] = field(default_factory=list)
    rewrite_required: bool = False
    safe_rewrite: str | None = None
    summary: str = "passed"
    critic_source: str = "rule"
    debug: dict[str, Any] | None = None
