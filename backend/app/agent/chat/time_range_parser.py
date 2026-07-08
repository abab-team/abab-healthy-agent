from __future__ import annotations

from datetime import date, timedelta
import re

from app.agent.chat.schemas import HealthQueryTimeRange


def parse_time_range(message: str, *, reference_date: date | None = None) -> HealthQueryTimeRange:
    today = reference_date or date.today()
    text = (message or "").lower()
    if "昨天" in text or "yesterday" in text:
        day = today - timedelta(days=1)
        return HealthQueryTimeRange(day, day, "yesterday", 1)
    if "今天" in text or "今日" in text or "today" in text:
        return HealthQueryTimeRange(today, today, "today", 1)
    if "上个月" in text or "last month" in text:
        first_this_month = today.replace(day=1)
        last_month_end = first_this_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        return HealthQueryTimeRange(last_month_start, last_month_end, "last_month", (last_month_end - last_month_start).days + 1)
    if "这个月" in text or "本月" in text or "this month" in text:
        start = today.replace(day=1)
        return HealthQueryTimeRange(start, today, "this_month", (today - start).days + 1)
    if "过去三个月" in text or "最近三个月" in text or "last 3 months" in text:
        return _last_days(today, 90, "last_90_days")
    if "最近一周" in text or "一周" in text or "近一周" in text or "last week" in text:
        return _last_days(today, 7, "last_7_days")
    match = re.search(r"(?:最近|过去|last)\s*(\d+)\s*(?:天|days?)", text)
    if match:
        days = max(1, min(int(match.group(1)), 365))
        return _last_days(today, days, f"last_{days}_days")
    if "最近30天" in text or "近30天" in text or "一个月" in text or "30 days" in text:
        return _last_days(today, 30, "last_30_days")
    return _last_days(today, 7, "last_7_days")


def _last_days(today: date, days: int, label: str) -> HealthQueryTimeRange:
    return HealthQueryTimeRange(today - timedelta(days=days - 1), today, label, days)
