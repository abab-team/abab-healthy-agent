from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DailyReportSnapshot:
    user_id: str
    has_report: bool
    message: str
    report_date: date | None
    status_level: str | None
    summary_text: str | None
    generation_status: str | None
