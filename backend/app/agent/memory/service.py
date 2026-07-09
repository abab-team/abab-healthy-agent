from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent import safety
from app.agent.chat.member_resolver import resolve_member_label
from app.agent.chat.schemas import HealthQueryPlan
from app.agent.chat.time_range_parser import parse_time_range
from app.agent.models import AgentMemoryItem, AgentMessage, AgentSession
from app.db.mixins import utc_now


SHORT_CONTEXT_LIMIT = 8
SAFE_SUMMARY_LENGTH = 500
FOLLOWUP_TIME_MARKERS = (
    "that period",
    "same period",
    "same time",
    "as before",
    "like before",
    "刚才",
    "一样",
    "同样",
    "上次",
)
LAST_MONTH_MARKERS = ("上个月", "last month")
LAST_30_DAY_MARKERS = ("最近30天", "最近 30 天", "过去30天", "过去 30 天", "30 days")
UNSAFE_MEMORY_MARKERS = (
    "diagnosis",
    "prescription",
    "dosage",
    "stop medication",
    "确诊",
    "诊断",
    "处方",
    "剂量",
    "停药",
    "高风险",
    "低风险",
    "正常",
    "异常",
)


@dataclass(frozen=True)
class SessionMemoryContext:
    last_intent: str | None = None
    last_member_label: str | None = None
    last_member_scope: str | None = None
    last_metric_type: str | None = None
    last_time_range_label: str | None = None
    last_time_range_days: int | None = None
    last_tool_name: str | None = None
    summary_lines: tuple[str, ...] = ()


def get_or_create_session(
    db: Session,
    *,
    user_id: UUID,
    session_id: UUID | str | None = None,
    family_id: UUID | None = None,
    title: str | None = None,
) -> AgentSession:
    if session_id is not None:
        existing = get_session_for_user(db, session_id=session_id, user_id=user_id)
        if existing is not None:
            existing.last_active_at = utc_now()
            if family_id is not None:
                existing.family_id = family_id
            db.flush()
            return existing

    session = AgentSession(
        user_id=user_id,
        family_id=family_id,
        title=safety.excerpt_text(title, max_length=120) if title else None,
        last_active_at=utc_now(),
    )
    db.add(session)
    db.flush()
    return session


def get_session_for_user(db: Session, *, session_id: UUID | str, user_id: UUID) -> AgentSession | None:
    parsed_session_id = _parse_uuid(session_id)
    if parsed_session_id is None:
        return None
    stmt = select(AgentSession).where(AgentSession.id == parsed_session_id, AgentSession.user_id == user_id)
    return db.scalar(stmt)


def list_sessions(db: Session, *, user_id: UUID, limit: int = 20) -> list[AgentSession]:
    stmt = (
        select(AgentSession)
        .where(AgentSession.user_id == user_id)
        .order_by(AgentSession.last_active_at.desc(), AgentSession.created_at.desc())
        .limit(max(1, min(limit, 100)))
    )
    return list(db.scalars(stmt))


def append_message(
    db: Session,
    *,
    session_id: UUID | str,
    role: str,
    content: str,
    intent: str | None = None,
    target_user_id: UUID | None = None,
    member_label: str | None = None,
    member_scope: str | None = None,
    metric_type: str | None = None,
    time_range_label: str | None = None,
    time_range_days: int | None = None,
    tool_name: str | None = None,
) -> AgentMessage | None:
    parsed_session_id = _parse_uuid(session_id)
    if parsed_session_id is None:
        return None
    session = db.get(AgentSession, parsed_session_id)
    if session is None:
        return None
    message = AgentMessage(
        session_id=parsed_session_id,
        role=role[:32],
        content_summary=safety.excerpt_text(content, max_length=SAFE_SUMMARY_LENGTH) or "",
        intent=intent[:100] if intent else None,
        target_user_id=target_user_id,
        member_label=safety.excerpt_text(member_label, max_length=64) if member_label else None,
        member_scope=member_scope[:32] if member_scope else None,
        metric_type=metric_type[:64] if metric_type else None,
        time_range_label=time_range_label[:64] if time_range_label else None,
        time_range_days=time_range_days,
        tool_name=tool_name[:100] if tool_name else None,
    )
    session.last_active_at = utc_now()
    db.add(message)
    db.flush()
    return message


def list_session_messages(db: Session, *, session_id: UUID | str, user_id: UUID, limit: int = 50) -> list[AgentMessage]:
    session = get_session_for_user(db, session_id=session_id, user_id=user_id)
    if session is None:
        return []
    stmt = (
        select(AgentMessage)
        .where(AgentMessage.session_id == session.id)
        .order_by(AgentMessage.created_at.asc())
        .limit(max(1, min(limit, 100)))
    )
    return list(db.scalars(stmt))


def load_session_context(db: Session, *, user_id: UUID, session_id: UUID | str | None) -> SessionMemoryContext:
    if session_id is None:
        return SessionMemoryContext()
    session = get_session_for_user(db, session_id=session_id, user_id=user_id)
    if session is None:
        return SessionMemoryContext()
    stmt = (
        select(AgentMessage)
        .where(AgentMessage.session_id == session.id)
        .order_by(AgentMessage.created_at.desc())
        .limit(SHORT_CONTEXT_LIMIT)
    )
    messages = list(db.scalars(stmt))
    reference = next(
        (
            message
            for message in messages
            if message.intent or message.metric_type or message.tool_name or message.time_range_label
        ),
        None,
    )
    return SessionMemoryContext(
        last_intent=reference.intent if reference else None,
        last_member_label=reference.member_label if reference else None,
        last_member_scope=reference.member_scope if reference else None,
        last_metric_type=reference.metric_type if reference else None,
        last_time_range_label=reference.time_range_label if reference else None,
        last_time_range_days=reference.time_range_days if reference else None,
        last_tool_name=reference.tool_name if reference else None,
        summary_lines=tuple(message.content_summary for message in reversed(messages) if message.content_summary),
    )


def apply_session_context(
    message: str,
    plan: HealthQueryPlan,
    context: SessionMemoryContext,
    *,
    reference_date: date | None = None,
) -> HealthQueryPlan:
    if not _has_followup_marker(message):
        return plan
    updates: dict[str, object | None] = {}
    if (plan.is_unknown or not plan.tool_name) and context.last_intent:
        updates["intent"] = type(plan.intent)(context.last_intent)
        updates["tool_name"] = context.last_tool_name
    if (plan.member_label is None or _mentions_followup_only(message)) and context.last_member_label:
        updates["member_label"] = context.last_member_label
        updates["member_scope"] = context.last_member_scope or "self"
    explicit_member_label, explicit_member_scope = resolve_member_label(message)
    if explicit_member_label:
        updates["member_label"] = explicit_member_label
        updates["member_scope"] = explicit_member_scope
    if (plan.metric_type is None or _mentions_followup_only(message)) and context.last_metric_type:
        updates["metric_type"] = context.last_metric_type
        tool_input = dict(updates.get("tool_input") or plan.tool_input or {})
        if (updates.get("tool_name") or plan.tool_name or context.last_tool_name) == "health_data.metric.summary":
            tool_input.setdefault("metric_type", context.last_metric_type)
            tool_input.setdefault("aggregation", plan.aggregation or "summary")
        updates["tool_input"] = tool_input
    if plan.tool_name is None and context.last_tool_name:
        updates["tool_name"] = context.last_tool_name
    if _contains_any(message, LAST_MONTH_MARKERS):
        time_range = parse_time_range("last month", reference_date=reference_date)
        updates["time_range"] = time_range
    elif _contains_any(message, LAST_30_DAY_MARKERS):
        time_range = parse_time_range("30 days", reference_date=reference_date)
        updates["time_range"] = time_range
    elif _contains_any(message, FOLLOWUP_TIME_MARKERS) and context.last_time_range_days:
        time_range = parse_time_range(f"last {context.last_time_range_days} days", reference_date=reference_date)
        updates["time_range"] = time_range

    if "time_range" in updates:
        tool_input = dict(updates.get("tool_input") or plan.tool_input or {})
        tool_input["days"] = updates["time_range"].days  # type: ignore[union-attr]
        updates["tool_input"] = tool_input
    return _replace_plan(plan, **updates)


def create_safe_preference_memory(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID | None,
    message: str,
) -> AgentMemoryItem | None:
    text = (message or "").strip()
    lowered = text.lower()
    if not text or _contains_any(lowered, UNSAFE_MEMORY_MARKERS):
        return None
    memory_type: str | None = None
    content: str | None = None
    if ("简洁" in text or "short" in lowered or "concise" in lowered) and ("以后" in text or "prefer" in lowered):
        memory_type = "response_preference"
        content = "用户希望回答保持简洁。"
    elif ("先看" in text and "覆盖" in text) or "coverage first" in lowered:
        memory_type = "response_preference"
        content = "用户希望回答时优先说明系统内记录覆盖情况。"
    elif ("常关注" in text or "经常看" in text) and ("血压" in text or "sleep" in lowered or "睡眠" in text):
        memory_type = "attention_focus"
        content = safety.excerpt_text(text, max_length=160)

    if memory_type is None or content is None:
        return None
    item = AgentMemoryItem(
        user_id=user_id,
        family_id=family_id,
        memory_type=memory_type,
        content=content,
        structured_data_json={"source": "chat_preference"},
        confidence=80,
        source="user_confirmed_preference",
        is_user_editable=True,
    )
    db.add(item)
    db.flush()
    return item


def list_memory_items(db: Session, *, user_id: UUID, limit: int = 100) -> list[AgentMemoryItem]:
    stmt = (
        select(AgentMemoryItem)
        .where(AgentMemoryItem.user_id == user_id, AgentMemoryItem.deleted_at.is_(None))
        .order_by(AgentMemoryItem.created_at.desc())
        .limit(max(1, min(limit, 200)))
    )
    return list(db.scalars(stmt))


def delete_memory_item(db: Session, *, user_id: UUID, memory_id: UUID | str) -> bool:
    parsed_memory_id = _parse_uuid(memory_id)
    if parsed_memory_id is None:
        return False
    stmt = select(AgentMemoryItem).where(
        AgentMemoryItem.id == parsed_memory_id,
        AgentMemoryItem.user_id == user_id,
        AgentMemoryItem.deleted_at.is_(None),
    )
    item = db.scalar(stmt)
    if item is None:
        return False
    item.deleted_at = utc_now()
    db.flush()
    return True


def _replace_plan(plan: HealthQueryPlan, **updates: object | None) -> HealthQueryPlan:
    data = {
        "intent": plan.intent,
        "time_range": plan.time_range,
        "member_label": plan.member_label,
        "member_scope": plan.member_scope,
        "metric_type": plan.metric_type,
        "source_type": plan.source_type,
        "aggregation": plan.aggregation,
        "tool_name": plan.tool_name,
        "tool_input": plan.tool_input,
        "safe_unknown_reason": plan.safe_unknown_reason,
    }
    data.update({key: value for key, value in updates.items() if value is not None})
    if data["tool_name"] is not None and data["safe_unknown_reason"] is not None:
        data["safe_unknown_reason"] = None
    return HealthQueryPlan(**data)  # type: ignore[arg-type]


def _parse_uuid(value: UUID | str) -> UUID | None:
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _has_followup_marker(message: str) -> bool:
    return _contains_any(message, (*FOLLOWUP_TIME_MARKERS, *LAST_MONTH_MARKERS, *LAST_30_DAY_MARKERS, "那", "呢"))


def _mentions_followup_only(message: str) -> bool:
    stripped = (message or "").strip().lower()
    return len(stripped) <= 24 or stripped in {"那上个月呢", "我妈呢", "我爸呢", "和刚才一样"}


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    lowered = (text or "").lower()
    return any(marker.lower() in lowered for marker in markers)
