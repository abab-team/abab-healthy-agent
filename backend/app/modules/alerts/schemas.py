from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AlertSummary:
    user_id: str
    count: int
    active_count: int
    due_count: int
    latest_alert: dict | None
    message: str
