from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from sqlalchemy.orm import Session

from app.modules.permissions.service import check_member_permission
from app.rag.schemas import RagIndexRecord, RagSourceType


ALLOWED_SOURCE_TYPES = frozenset(item.value for item in RagSourceType)
DEFAULT_SOURCE_TYPES = tuple(RagSourceType)
FORBIDDEN_TEXT_MARKERS = (
    "raw_text",
    "symptom_text",
    "raw_extracted_text",
    "file_path",
    "api_key",
    "private_key",
    "password",
    "token",
    "traceback",
    "select ",
    "insert ",
    "update ",
    "delete ",
    "c:\\",
    "/home/",
    "/mnt/",
    "file://",
)
SOURCE_PERMISSION_MAP: dict[RagSourceType, tuple[str, str]] = {
    RagSourceType.HEALTH_PROFILE_SUMMARY: ("profile", "view"),
    RagSourceType.BLOOD_PRESSURE_SUMMARY: ("metrics", "view"),
    RagSourceType.SYMPTOM_RECORD_SUMMARY: ("symptoms", "view"),
    RagSourceType.MEDICAL_EVENT_SUMMARY: ("medical_events", "view"),
    RagSourceType.MEDICAL_EVENT_DRAFT_SUMMARY: ("medical_events", "view"),
    RagSourceType.MEDICAL_DOCUMENT_METADATA: ("documents", "view"),
    RagSourceType.DOCUMENT_EXTRACTION_PREVIEW: ("documents", "view"),
    RagSourceType.OCR_EXTRACTION_PREVIEW: ("documents", "view"),
    RagSourceType.DAILY_REPORT_SUMMARY: ("reports", "view"),
    RagSourceType.ALERT_SUMMARY: ("alerts", "view"),
    RagSourceType.AGENT_GENERATED_BRIEF_SUMMARY: ("memory_summary", "view"),
}


def permission_for_source_type(source_type: RagSourceType) -> tuple[str, str]:
    return SOURCE_PERMISSION_MAP[source_type]


def coerce_source_types(values: Iterable[str] | None) -> tuple[RagSourceType, ...]:
    if values is None:
        return DEFAULT_SOURCE_TYPES
    result: list[RagSourceType] = []
    for value in values:
        try:
            source_type = RagSourceType(str(value))
        except ValueError as exc:
            raise ValueError(f"source_type is not allowed: {value}") from exc
        if source_type not in result:
            result.append(source_type)
    return tuple(result)


def validate_index_record(record: RagIndexRecord) -> RagIndexRecord:
    text_parts = [record.title, record.summary_text, record.safe_excerpt]
    text_parts.extend(str(value) for value in record.metadata_safe.values() if value is not None)
    joined = " ".join(text_parts)
    if contains_forbidden_marker(joined):
        raise ValueError("RAG source contains unsafe content")
    if not record.safe_excerpt.strip():
        raise ValueError("RAG source safe_excerpt is required")
    return record


def contains_forbidden_marker(text: str | None) -> bool:
    lowered = str(text or "").lower()
    return any(marker in lowered for marker in FORBIDDEN_TEXT_MARKERS)


def safe_text(value: Any, *, max_length: int = 1200) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        text = "; ".join(safe_text(item, max_length=200) for item in value)
    elif isinstance(value, Mapping):
        safe_pairs = []
        for key, item in value.items():
            key_text = str(key)
            if contains_forbidden_marker(key_text):
                continue
            item_text = safe_text(item, max_length=200)
            if item_text:
                safe_pairs.append(f"{key_text}: {item_text}")
        text = "; ".join(safe_pairs)
    else:
        text = str(value)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    text = " ".join(text.split())
    if contains_forbidden_marker(text):
        return "[redacted]"
    return text[:max_length]


def safe_metadata(values: Mapping[str, Any]) -> dict[str, str | int | float | bool | None]:
    result: dict[str, str | int | float | bool | None] = {}
    for key, value in values.items():
        key_text = str(key)
        if contains_forbidden_marker(key_text):
            continue
        if isinstance(value, bool) or value is None:
            result[key_text] = value
        elif isinstance(value, (int, float)):
            result[key_text] = value
        else:
            cleaned = safe_text(value, max_length=200)
            if cleaned != "[redacted]":
                result[key_text] = cleaned
    return result


def has_record_permission(
    db: Session,
    *,
    current_user_id,
    record: RagIndexRecord,
) -> bool:
    if current_user_id == record.target_user_id:
        return True
    if record.family_id is None:
        return False
    decision = check_member_permission(
        db,
        current_user_id=current_user_id,
        family_id=record.family_id,
        target_user_id=record.target_user_id,
        permission_type=record.permission_type,
        action=record.permission_action,
    )
    return decision.allowed


def has_any_requested_permission(
    db: Session,
    *,
    current_user_id,
    target_user_id,
    family_id,
    source_types: Iterable[RagSourceType],
) -> bool:
    if current_user_id == target_user_id:
        return True
    if family_id is None:
        return False
    for source_type in source_types:
        permission_type, action = permission_for_source_type(source_type)
        decision = check_member_permission(
            db,
            current_user_id=current_user_id,
            family_id=family_id,
            target_user_id=target_user_id,
            permission_type=permission_type,
            action=action,
        )
        if decision.allowed:
            return True
    return False
