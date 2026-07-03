from __future__ import annotations

from decimal import Decimal


def data_quality_for_count(count: int) -> str:
    if count >= 10:
        return "good"
    if count >= 3:
        return "partial"
    if count >= 1:
        return "insufficient"
    return "missing"


def to_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)
