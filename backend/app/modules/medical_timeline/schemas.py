from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MedicalEventSummary:
    days: int
    count: int
    follow_up_needed_count: int
    latest_event: dict | None
    events: list[dict]
