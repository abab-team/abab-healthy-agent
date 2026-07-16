"""Server-owned business capabilities for the conversation Agent.

The LLM sees only these capability names.  It never receives internal tool
names, identifiers, database handles, or permission decisions.  This adapter
resolves a human member reference on the server and delegates every underlying
read to :class:`AgentToolExecutor`.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Any
from uuid import uuid4

from app.agent.chat import HealthQueryIntent, HealthQueryPlan, HealthQueryTimeRange
from app.agent.chat.family_context import resolve_family_target
from app.agent.schemas import AgentWorkflowContext, ToolExecutionRequest, ToolExecutionResult
from app.agent.tool_executor import AgentToolExecutor
from app.agent.conversation_v2.tool_runtime import safe_tool_result


ALLOWED_CAPABILITIES = {
    "health_overview",
    "metric_detail",
    "medical_history",
    "document_overview",
    "alert_overview",
}
ALLOWED_METRICS = {"blood_pressure", "sleep", "weight", "steps", "heart_rate", "bmi"}
PERIOD_DAYS = {"7d": 7, "30d": 30, "90d": 90, "365d": 365}
_METRIC_TYPES = {
    "sleep": "sleep_duration",
    "weight": "weight",
    "steps": "steps",
    "heart_rate": "heart_rate",
}


@dataclass(frozen=True)
class BusinessToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class BusinessToolExecution:
    tool_message: dict[str, Any]
    underlying_results: tuple[ToolExecutionResult, ...]
    allowed: bool


class ConversationBusinessToolRuntime:
    """Validate a business call and use the existing ToolExecutor only."""

    def __init__(self, *, context: AgentWorkflowContext, executor: AgentToolExecutor) -> None:
        self.context = context
        self.executor = executor

    def validate(self, raw: dict[str, Any]) -> BusinessToolCall | None:
        name = str(raw.get("name") or "")
        arguments = raw.get("args") if isinstance(raw.get("args"), dict) else raw.get("arguments")
        if name not in ALLOWED_CAPABILITIES or not isinstance(arguments, dict):
            return None
        if set(arguments) - {"subject_reference", "period", "metric"}:
            return None
        subject = str(arguments.get("subject_reference") or "self").strip()[:80]
        period = str(arguments.get("period") or "7d").strip()
        metric = str(arguments.get("metric") or "").strip()
        if period not in PERIOD_DAYS:
            return None
        if name == "metric_detail" and metric not in ALLOWED_METRICS:
            return None
        if name != "metric_detail" and metric:
            return None
        return BusinessToolCall(
            id=str(raw.get("id") or f"business_{uuid4().hex}"),
            name=name,
            arguments={"subject_reference": subject, "period": period, **({"metric": metric} if metric else {})},
        )

    def execute(self, call: BusinessToolCall) -> BusinessToolExecution:
        plan = self._server_plan(call)
        resolution = resolve_family_target(self.context, plan)
        subject_label = resolution.display_name or ("我" if plan.member_scope == "self" else plan.member_label or "该成员")
        if resolution.request is None:
            return BusinessToolExecution(
                tool_message=_blocked_fact(call, subject_label, "该成员暂时不可查询。"),
                underlying_results=(),
                allowed=False,
            )
        execution_context = replace(self.context, request=resolution.request)
        results: list[ToolExecutionResult] = []
        for tool_name, args in self._underlying_calls(call):
            results.append(
                self.executor.execute(
                    execution_context.db,
                    ToolExecutionRequest(
                        trace_id=execution_context.trace_id,
                        tool_name=tool_name,
                        actor_user_id=execution_context.request.actor_user_id,
                        target_user_id=execution_context.request.target_user_id,
                        family_id=execution_context.request.family_id,
                        input_data=args,
                        confirmed=False,
                        safety_level=execution_context.safety_level,
                        reason="conversation_runtime_v3_business_capability",
                    ),
                )
            )
        safe_results = [safe_tool_result(item) for item in results]
        return BusinessToolExecution(
            tool_message=_safe_fact_package(call, subject_label, safe_results),
            underlying_results=tuple(results),
            allowed=all(not item.blocked for item in results),
        )

    def _server_plan(self, call: BusinessToolCall) -> HealthQueryPlan:
        days = PERIOD_DAYS[call.arguments["period"]]
        subject = call.arguments["subject_reference"]
        self_reference = subject.lower() in {"self", "me", "我", "本人", "我自己"}
        return HealthQueryPlan(
            intent=HealthQueryIntent.QUERY_DAILY_STATUS,
            time_range=HealthQueryTimeRange(date.today() - timedelta(days=days - 1), date.today(), call.arguments["period"], days),
            member_label=None if self_reference else subject,
            member_scope="self" if self_reference else "family",
            planner_source="conversation_runtime_v3_guard",
        )

    def _underlying_calls(self, call: BusinessToolCall) -> tuple[tuple[str, dict[str, Any]], ...]:
        days = PERIOD_DAYS[call.arguments["period"]]
        name = call.name
        if name == "health_overview":
            return (
                ("health_profile.get", {}),
                ("health_data.blood_pressure.summary", {"days": days}),
                ("health_data.metrics.recent", {"days": days, "limit": 10}),
                ("health_record.symptoms.query", {"days": days}),
                ("medical_timeline.events.query", {"days": days}),
                ("documents.query", {"limit": 10}),
                ("alerts.query", {"limit": 10}),
            )
        if name == "metric_detail":
            metric = call.arguments["metric"]
            if metric == "blood_pressure":
                return (("health_data.blood_pressure.summary", {"days": days}),)
            if metric == "bmi":
                return (("health_profile.get", {}), ("health_data.metric.summary", {"metric_type": "weight", "days": days, "aggregation": "summary"}))
            return (("health_data.metric.summary", {"metric_type": _METRIC_TYPES[metric], "days": days, "aggregation": "summary"}),)
        if name == "medical_history":
            return (("medical_timeline.events.query", {"days": days}), ("documents.query", {"limit": 10}))
        if name == "document_overview":
            return (("documents.query", {"limit": 10}),)
        return (("alerts.query", {"limit": 10}),)


def _blocked_fact(call: BusinessToolCall, subject_label: str, note: str) -> dict[str, Any]:
    return {
        "capability": call.name,
        "subject_label": subject_label,
        "period": call.arguments.get("period"),
        "context": {
            "subject_reference": "self" if str(call.arguments.get("subject_reference") or "").lower() in {"self", "me"} else "family_member",
            "subject_label": subject_label,
            "topic": call.name,
            "last_business_capability": call.name,
            "last_fact_type": call.name,
            "last_time_range": str(call.arguments.get("period") or ""),
        },
        "facts": {},
        "unavailable_sections": ["requested_data"],
        "safe_next_actions": [],
        "note": note,
    }


def _safe_fact_package(call: BusinessToolCall, subject_label: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    facts: dict[str, Any] = {}
    unavailable: list[str] = []
    for result in results:
        tool = str(result.get("tool") or "")
        if result.get("blocked") or result.get("status") != "completed":
            unavailable.append(_section_name(tool))
            continue
        summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
        count = result.get("count")
        if tool == "health_profile.get":
            facts["profile"] = {"available": not bool(result.get("empty"))}
        elif tool == "health_data.blood_pressure.summary":
            facts["blood_pressure"] = _compact_blood_pressure(summary, count)
        elif tool == "health_data.metric.summary":
            metric = str(summary.get("metric_type") or "metric")
            facts[metric] = _compact_metric(summary, count)
        elif tool == "health_data.metrics.recent":
            facts["metrics"] = {"record_count": count or 0}
        elif tool == "health_record.symptoms.query":
            facts["symptoms"] = {"record_count": count or 0}
        elif tool == "medical_timeline.events.query":
            facts["medical_events"] = {"record_count": count or 0}
        elif tool == "documents.query":
            facts["documents"] = {"record_count": count or 0}
        elif tool == "alerts.query":
            facts["alerts"] = {"record_count": count or 0}
    return {
        "capability": call.name,
        "subject_label": subject_label,
        "period": call.arguments.get("period"),
        "metric": call.arguments.get("metric"),
        # The conversation layer consumes this compact aggregate instead of
        # raw underlying tool payloads.  It is an expression-ready fact bag,
        # not a new health model or a permission decision.
        "overview": facts if call.name == "health_overview" else {},
        "context": {
            "subject_reference": "self" if str(call.arguments.get("subject_reference") or "").lower() in {"self", "me"} else "family_member",
            "subject_label": subject_label,
            "topic": call.name,
            "last_business_capability": call.name,
            "last_fact_type": "health_overview" if call.name == "health_overview" else str(call.arguments.get("metric") or call.name),
            "last_time_range": str(call.arguments.get("period") or ""),
        },
        "facts": facts,
        "unavailable_sections": sorted(set(unavailable)),
        "safe_next_actions": ["查看更长时间范围", "查看其他已记录项目"],
    }


def _compact_blood_pressure(summary: dict[str, Any], count: Any) -> dict[str, Any]:
    latest_s, latest_d = summary.get("latest_systolic"), summary.get("latest_diastolic")
    average_s, average_d = summary.get("avg_systolic"), summary.get("avg_diastolic")
    return {
        "record_count": int(count or 0),
        "latest": f"{latest_s}/{latest_d} mmHg" if latest_s is not None and latest_d is not None else None,
        "average": f"{average_s:.0f}/{average_d:.0f} mmHg" if isinstance(average_s, (int, float)) and isinstance(average_d, (int, float)) else None,
    }


def _compact_metric(summary: dict[str, Any], count: Any) -> dict[str, Any]:
    return {"record_count": int(count or 0), "latest": summary.get("latest_value"), "average": summary.get("avg_value"), "unit": summary.get("unit")}


def _section_name(tool: str) -> str:
    return {"health_profile.get": "profile", "health_data.blood_pressure.summary": "blood_pressure", "health_data.metrics.recent": "metrics", "health_record.symptoms.query": "symptoms", "medical_timeline.events.query": "medical_events", "documents.query": "documents", "alerts.query": "alerts"}.get(tool, "requested_data")
