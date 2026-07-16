"""Controlled ToolExecutor bridge for Conversation Runtime V2.

The LangGraph nodes call this adapter, never repositories or health services.
It resolves a family reference on the server, injects identity into a
``ToolExecutionRequest``, and delegates permission and execution checks to the
existing ``AgentToolExecutor``.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
import json
from typing import Any
from uuid import UUID, uuid4

from app.agent.chat import HealthQueryIntent, HealthQueryPlan, HealthQueryTimeRange, parse_health_query
from app.agent.chat.family_context import resolve_family_target
from app.agent.schemas import AgentWorkflowContext, ToolExecutionRequest, ToolExecutionResult
from app.agent.tool_executor import AgentToolExecutor


MAX_TOOLS_PER_TURN = 3
MAX_GRAPH_TOOL_STEPS = 4
FORBIDDEN_ARGUMENT_KEYS = {
    "actor_user_id", "current_user_id", "target_user_id", "family_id",
    "tool_name", "input_data", "sql", "db", "_db", "file_path",
}

_INTENT_TOOL_MAP = {
    HealthQueryIntent.QUERY_METRICS: ("health_data.metric.summary",),
    HealthQueryIntent.QUERY_BLOOD_PRESSURE: ("health_data.blood_pressure.summary",),
    HealthQueryIntent.QUERY_SYMPTOMS: ("health_record.symptoms.query",),
    HealthQueryIntent.QUERY_MEDICAL_EVENTS: ("medical_timeline.events.query",),
    HealthQueryIntent.QUERY_DOCUMENTS: ("documents.query",),
    HealthQueryIntent.QUERY_ALERTS: ("alerts.query",),
    HealthQueryIntent.QUERY_MEDICAL_HISTORY: (
        "health_profile.get",
        "medical_timeline.events.query",
        "documents.query",
    ),
    # The overview stays bounded in V2.  It can be expanded through a future
    # explicit overview tool without allowing arbitrary model-selected tools.
    HealthQueryIntent.QUERY_DAILY_STATUS: (
        "health_data.metrics.recent",
        "health_data.blood_pressure.summary",
        "health_record.symptoms.query",
    ),
}


@dataclass(frozen=True)
class PlannedToolCall:
    id: str
    name: str
    args: dict[str, Any]


@dataclass(frozen=True)
class ConversationToolPlan:
    plan: HealthQueryPlan | None
    calls: tuple[PlannedToolCall, ...] = ()
    reason: str | None = None


class ConversationToolRuntime:
    """Server-owned planner validation and ToolExecutor entry point."""

    def __init__(self, *, context: AgentWorkflowContext, executor: AgentToolExecutor) -> None:
        self.context = context
        self.executor = executor

    def plan(
        self,
        message: str,
        *,
        previous_plan_summary: dict[str, Any] | None = None,
    ) -> ConversationToolPlan:
        """Convert a constrained health intent into a fixed registered tool set.

        ``parse_health_query`` may identify an intent, but its historical
        ``tool_name`` field is deliberately ignored.  This server-owned map is
        the only route from intent to a tool name.
        """
        plan = _apply_conversation_context(
            parse_health_query(message),
            message,
            previous_plan_summary,
        )
        names = _INTENT_TOOL_MAP.get(plan.intent, ())
        if not names:
            return ConversationToolPlan(plan=plan, reason="no_readonly_tool_plan")
        if len(names) > MAX_TOOLS_PER_TURN:
            return ConversationToolPlan(plan=plan, reason="tool_limit_exceeded")

        calls: list[PlannedToolCall] = []
        for name in names:
            args = _safe_args_for_plan(plan, name)
            if not self._validate_call(name, args):
                return ConversationToolPlan(plan=plan, reason="invalid_tool_plan")
            calls.append(PlannedToolCall(id=f"call_{uuid4().hex}", name=name, args=args))
        return ConversationToolPlan(plan=plan, calls=tuple(calls))

    def execute(self, plan: HealthQueryPlan, calls: list[dict[str, Any]]) -> tuple[list[ToolExecutionResult], dict[str, str | bool | None]]:
        """Resolve target on every execution and run each read-only call once."""
        if len(calls) > MAX_TOOLS_PER_TURN:
            return [], {"allowed": False, "reason": "tool_limit_exceeded", "member": None}

        resolution = resolve_family_target(self.context, plan)
        if resolution.request is None:
            return (
                [_safe_failed_result(str(call.get("name") or "unknown"), "member_not_resolved") for call in calls],
                {"allowed": False, "reason": "member_not_resolved", "member": plan.member_label},
            )
        execution_context = replace(self.context, request=resolution.request)
        results: list[ToolExecutionResult] = []
        for call in calls:
            name = str(call.get("name") or "")
            args = call.get("args") if isinstance(call.get("args"), dict) else {}
            if not self._validate_call(name, args):
                results.append(_safe_failed_result(name, "invalid_tool_arguments"))
                continue
            result = self.executor.execute(
                execution_context.db,
                ToolExecutionRequest(
                    trace_id=execution_context.trace_id,
                    tool_name=name,
                    actor_user_id=execution_context.request.actor_user_id,
                    target_user_id=execution_context.request.target_user_id,
                    family_id=execution_context.request.family_id,
                    input_data=args,
                    confirmed=False,
                    safety_level=execution_context.safety_level,
                    reason="conversation_runtime_v2",
                ),
            )
            results.append(result)
        return results, {
            "allowed": all(not result.blocked for result in results),
            "reason": None if all(not result.blocked for result in results) else "permission_or_tool_blocked",
            "member": resolution.display_name,
        }

    def _validate_call(self, name: str, args: dict[str, Any]) -> bool:
        if not name or any(key in FORBIDDEN_ARGUMENT_KEYS for key in args):
            return False
        try:
            tool = self.executor.registry.ensure_tool_allowed(name)
        except Exception:
            return False
        metadata = tool.metadata
        if metadata.access_mode != "read" or metadata.requires_confirmation:
            return False
        try:
            # Validate schema before permission/execution.  The actual executor
            # validates again, preserving its existing gate.
            tool.validate_input(dict(args))
        except Exception:
            return False
        return True


def safe_tool_result(result: ToolExecutionResult) -> dict[str, Any]:
    """Compact ToolMessage payload with an explicit safe field allowlist."""
    data = result.output_data or {}
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    safe_summary = {
        key: _safe_scalar(summary.get(key))
        for key in (
            "metric_type", "days", "count", "latest_value", "avg_value",
            "min_value", "max_value", "unit", "trend_direction",
            "latest_systolic", "latest_diastolic", "latest_pulse",
            "avg_systolic", "avg_diastolic", "min_systolic", "max_systolic",
            "min_diastolic", "max_diastolic", "latest_measured_at",
        )
        if summary.get(key) is not None
    }
    return {
        "tool": result.tool_name,
        "status": result.status,
        "blocked": result.blocked,
        "error_code": result.error_code,
        "count": _safe_count(data, summary),
        "empty": bool(data.get("empty", False)),
        "summary": safe_summary,
        "coverage_note": _safe_text(data.get("coverage_note"), 180),
    }


def tool_message_content(result: ToolExecutionResult) -> str:
    return json.dumps(safe_tool_result(result), ensure_ascii=False, separators=(",", ":"))


def _safe_args_for_plan(plan: HealthQueryPlan, tool_name: str) -> dict[str, Any]:
    days = max(1, min(plan.time_range.days, 365))
    if tool_name == "health_data.metric.summary":
        return {"metric_type": plan.metric_type or "sleep_duration", "days": days, "aggregation": plan.aggregation or "summary"}
    if tool_name == "health_data.metrics.recent":
        return {"days": days, "limit": 10}
    if tool_name in {"health_data.blood_pressure.summary", "health_record.symptoms.query"}:
        return {"days": days}
    if tool_name in {"medical_timeline.events.query", "alerts.query"}:
        return {"days": days, "limit": 10}
    if tool_name == "documents.query":
        return {"limit": 10}
    if tool_name == "health_profile.get":
        return {}
    return {"days": days}


def _apply_conversation_context(
    plan: HealthQueryPlan,
    message: str,
    previous: dict[str, Any] | None,
) -> HealthQueryPlan:
    """Carry only server-produced member/time context across a short follow-up.

    The persisted plan summary is checkpoint metadata, not a legacy ``last_*``
    field and never contains user identifiers.  Explicit references always win.
    """
    if not previous:
        return plan
    text = message.lower()
    prior = _plan_from_summary(previous)
    if prior is None:
        return plan
    if _is_time_range_continuation(text):
        return replace(prior, time_range=plan.time_range)
    if _is_overview_expansion(text):
        return replace(
            prior,
            intent=HealthQueryIntent.QUERY_DAILY_STATUS,
            source_type="daily_status",
            metric_type=None,
            aggregation="summary",
        )
    if prior.member_scope == "family" and not _has_explicit_member_reference(text):
        plan = replace(plan, member_scope="family", member_label=prior.member_label)
    return plan


def _plan_from_summary(summary: dict[str, Any]) -> HealthQueryPlan | None:
    try:
        intent = HealthQueryIntent(str(summary.get("intent")))
        days = max(1, min(int(summary.get("days") or 7), 365))
    except (TypeError, ValueError):
        return None
    end_date = date.today()
    return HealthQueryPlan(
        intent=intent,
        time_range=HealthQueryTimeRange(
            end_date - timedelta(days=days - 1),
            end_date,
            str(summary.get("time_range_label") or f"last_{days}_days"),
            days,
        ),
        member_label=_safe_text(summary.get("member_label"), 80),
        member_scope="family" if summary.get("member_scope") == "family" else "self",
        metric_type=_safe_text(summary.get("metric_type"), 40),
        aggregation="summary",
    )


def _has_explicit_member_reference(text: str) -> bool:
    return any(term in text for term in ("我", "本人", "自己", "爸爸", "父亲", "我爸", "妈妈", "母亲", "我妈"))


def _is_overview_expansion(text: str) -> bool:
    return any(term in text for term in ("不只是血压", "除了血压", "还有什么", "整体情况", "健康情况"))


def _is_time_range_continuation(text: str) -> bool:
    return any(term in text for term in ("最近30天", "30天", "30 天", "一个月", "上个月", "最近一周", "7天", "7 天"))


def _safe_count(data: dict[str, Any], summary: dict[str, Any]) -> int | None:
    value = data.get("count", summary.get("count"))
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _safe_text(value: Any, maximum: int) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.replace("\n", " ").strip()
    return text[:maximum] or None


def _safe_scalar(value: Any) -> str | int | float | bool | None:
    """Keep checkpoint payloads JSON-serializable and compact."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return None


def _safe_failed_result(name: str, error_code: str) -> ToolExecutionResult:
    return ToolExecutionResult(
        tool_name=name,
        status="failed",
        blocked=True,
        requires_confirmation=False,
        message="The requested system record could not be retrieved safely.",
        output_data=None,
        error_code=error_code,
    )
