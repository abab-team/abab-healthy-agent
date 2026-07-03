from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SymptomSummary:
    days: int
    count: int
    active_count: int
    follow_up_needed_count: int
    latest_record: dict | None
    common_symptoms: list[dict]
    records: list[dict]
