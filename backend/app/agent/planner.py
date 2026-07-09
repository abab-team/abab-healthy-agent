from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import json
from typing import Any

from app.agent.chat.schemas import HealthQueryIntent, HealthQueryPlan, HealthQueryTimeRange
from app.agent.prompts import PromptRegistry, get_prompt_registry
from app.core.config import Settings, get_settings
from app.llm.client import LLMClient, get_llm_client
from app.llm.schemas import LLMResponse


ALLOWED_METRIC_TYPES = (
    "sleep_duration",
    "steps",
    "weight",
    "heart_rate",
    "bmi",
    "exercise_duration",
    "blood_pressure",
)
ALLOWED_MEMBER_SCOPES = ("self", "father", "mother", "family")
ALLOWED_TIME_RANGES = (
    "today",
    "yesterday",
    "last_7_days",
    "last_30_days",
    "this_month",
    "last_month",
    "last_90_days",
)
ALLOWED_AGGREGATIONS = ("summary", "avg", "count", "latest", "sum")
FORBIDDEN_PLAN_KEYS = {"tool_name", "input_data", "current_user_id", "target_user_id", "family_id", "sql"}

INTENT_TOOL_MAP = {
    HealthQueryIntent.QUERY_METRICS: "health_data.metric.summary",
    HealthQueryIntent.QUERY_BLOOD_PRESSURE: "health_data.blood_pressure.summary",
    HealthQueryIntent.QUERY_SYMPTOMS: "health_record.symptoms.query",
    HealthQueryIntent.QUERY_MEDICAL_EVENTS: "medical_timeline.events.query",
    HealthQueryIntent.QUERY_DOCUMENTS: "documents.query",
    HealthQueryIntent.QUERY_ALERTS: "alerts.query",
    HealthQueryIntent.QUERY_DAILY_STATUS: "health_data.metrics.recent",
}


@dataclass(frozen=True)
class PlannerResult:
    plan: HealthQueryPlan
    llm_used: bool
    accepted: bool
    reason_code: str
    raw_response_summary: str | None = None


class LLMPlannerService:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        prompt_registry: PromptRegistry | None = None,
        llm_client: LLMClient | Any | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.prompt_registry = prompt_registry or get_prompt_registry()
        self.llm_client = llm_client

    def plan(
        self,
        *,
        user_message: str,
        recent_session_context_summary: tuple[str, ...] = (),
        safe_memory_summary: tuple[str, ...] = (),
        reference_date: date | None = None,
    ) -> PlannerResult:
        fallback = _unknown_plan(
            reason_code="llm_planner_unavailable",
            reference_date=reference_date,
            clarification_question="Please clarify which system record you want to query.",
        )
        if not self.settings.LLM_PLANNER_ENABLED:
            return PlannerResult(fallback, llm_used=False, accepted=False, reason_code="llm_planner_disabled")
        try:
            response = self._call_llm(
                user_message=user_message,
                recent_session_context_summary=recent_session_context_summary,
                safe_memory_summary=safe_memory_summary,
            )
            payload = _parse_json_object(response.content)
            validation = validate_llm_plan(
                payload,
                settings=self.settings,
                reference_date=reference_date,
            )
            return PlannerResult(
                validation.plan,
                llm_used=True,
                accepted=validation.accepted,
                reason_code=validation.reason_code,
                raw_response_summary=_safe_response_summary(response),
            )
        except Exception:
            return PlannerResult(
                _unknown_plan(
                    reason_code="llm_planner_failed",
                    reference_date=reference_date,
                    clarification_question="Please clarify which system record you want to query.",
                ),
                llm_used=True,
                accepted=False,
                reason_code="llm_planner_failed",
            )

    def _call_llm(
        self,
        *,
        user_message: str,
        recent_session_context_summary: tuple[str, ...],
        safe_memory_summary: tuple[str, ...],
    ) -> LLMResponse:
        prompt = self.prompt_registry.get_prompt("health_query_planner", version="v1")
        user_prompt = prompt.render(
            {
                "user_message": _safe_excerpt(user_message, 500),
                "recent_session_context_summary": tuple(_safe_excerpt(line, 160) for line in recent_session_context_summary[-6:]),
                "safe_memory_summary": tuple(_safe_excerpt(line, 160) for line in safe_memory_summary[-6:]),
                "allowed_intents": prompt.allowed_intents,
                "allowed_metric_types": ALLOWED_METRIC_TYPES,
                "allowed_member_scopes": ALLOWED_MEMBER_SCOPES,
                "allowed_time_ranges": ALLOWED_TIME_RANGES,
            }
        )
        client = self.llm_client or get_llm_client(self.settings)
        return client.generate_text(
            system_prompt=(
                "You are a constrained JSON planner. Return JSON only. "
                "Never call tools, choose tool names, query databases, or write data."
            ),
            user_prompt=user_prompt,
            temperature=0.0,
            max_tokens=300,
            metadata={
                "workflow_type": "chat_workflow",
                "prompt_name": "health_query_planner_v1",
                "prompt_version": prompt.version,
            },
        )


@dataclass(frozen=True)
class PlanValidationResult:
    accepted: bool
    plan: HealthQueryPlan
    reason_code: str


def validate_llm_plan(
    payload: dict[str, Any],
    *,
    settings: Settings | None = None,
    reference_date: date | None = None,
) -> PlanValidationResult:
    current_settings = settings or get_settings()
    forbidden = FORBIDDEN_PLAN_KEYS.intersection(payload.keys())
    if forbidden:
        return _validation_reject("llm_plan_forbidden_keys", reference_date=reference_date)

    if bool(payload.get("needs_clarification")):
        question = _safe_excerpt(payload.get("clarification_question") or "Please clarify your query.", 160)
        return _validation_reject(
            "llm_plan_needs_clarification",
            reference_date=reference_date,
            clarification_question=question,
        )

    confidence = _coerce_float(payload.get("confidence"))
    if confidence is None or confidence < current_settings.LLM_PLANNER_CONFIDENCE_THRESHOLD:
        return _validation_reject(
            "llm_plan_low_confidence",
            reference_date=reference_date,
            clarification_question="Please clarify who and which time range you want to query.",
        )

    try:
        intent = HealthQueryIntent(str(payload.get("intent") or "unknown"))
    except ValueError:
        return _validation_reject("llm_plan_invalid_intent", reference_date=reference_date)
    if intent == HealthQueryIntent.UNKNOWN or intent not in INTENT_TOOL_MAP:
        return _validation_reject("llm_plan_unknown_intent", reference_date=reference_date)

    metric_type = payload.get("metric_type")
    if metric_type is not None:
        metric_type = str(metric_type)
        if metric_type not in ALLOWED_METRIC_TYPES:
            return _validation_reject("llm_plan_invalid_metric_type", reference_date=reference_date)
    if intent == HealthQueryIntent.QUERY_METRICS and not metric_type:
        return _validation_reject(
            "llm_plan_missing_metric_type",
            reference_date=reference_date,
            clarification_question="Please clarify which metric you want to query.",
        )
    if intent == HealthQueryIntent.QUERY_BLOOD_PRESSURE:
        metric_type = "blood_pressure"

    member_label, member_scope = _member_from_scope(payload.get("member_scope"))
    if member_scope is None:
        return _validation_reject("llm_plan_invalid_member_scope", reference_date=reference_date)

    time_range = _time_range_from_label(str(payload.get("time_range") or "last_7_days"), reference_date=reference_date)
    if time_range is None:
        return _validation_reject("llm_plan_invalid_time_range", reference_date=reference_date)

    aggregation = str(payload.get("aggregation") or "summary")
    if aggregation not in ALLOWED_AGGREGATIONS:
        return _validation_reject("llm_plan_invalid_aggregation", reference_date=reference_date)

    plan = HealthQueryPlan(
        intent=intent,
        time_range=time_range,
        member_label=member_label,
        member_scope=member_scope,
        metric_type=metric_type,
        source_type=_source_type_for_intent(intent),
        aggregation=aggregation,
        tool_name=INTENT_TOOL_MAP[intent],
        tool_input=_tool_input_for_plan(intent, time_range, metric_type, aggregation),
        confidence=confidence,
        planner_source="llm",
    )
    return PlanValidationResult(True, plan, "llm_plan_accepted")


def _validation_reject(
    reason_code: str,
    *,
    reference_date: date | None = None,
    clarification_question: str | None = None,
) -> PlanValidationResult:
    return PlanValidationResult(
        False,
        _unknown_plan(
            reason_code=reason_code,
            reference_date=reference_date,
            clarification_question=clarification_question,
        ),
        reason_code,
    )


def _unknown_plan(
    *,
    reason_code: str,
    reference_date: date | None = None,
    clarification_question: str | None = None,
) -> HealthQueryPlan:
    return HealthQueryPlan(
        intent=HealthQueryIntent.UNKNOWN,
        time_range=_last_days(reference_date or date.today(), 7, "last_7_days"),
        safe_unknown_reason=reason_code,
        needs_clarification=bool(clarification_question),
        clarification_question=clarification_question,
        planner_source="llm",
    )


def _parse_json_object(content: str) -> dict[str, Any]:
    text = (content or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("planner output must be a JSON object")
    return parsed


def _member_from_scope(value: Any) -> tuple[str | None, str | None]:
    scope = str(value or "self").lower().strip()
    if scope in {"self", "me", "myself"}:
        return None, "self"
    if scope in {"father", "dad"}:
        return "father", "family"
    if scope in {"mother", "mom"}:
        return "mother", "family"
    if scope == "family":
        return "family member", "family"
    return None, None


def _time_range_from_label(label: str, *, reference_date: date | None = None) -> HealthQueryTimeRange | None:
    today = reference_date or date.today()
    normalized = label.lower().strip()
    if normalized == "today":
        return HealthQueryTimeRange(today, today, "today", 1)
    if normalized == "yesterday":
        day = today - timedelta(days=1)
        return HealthQueryTimeRange(day, day, "yesterday", 1)
    if normalized == "last_7_days":
        return _last_days(today, 7, "last_7_days")
    if normalized == "last_30_days":
        return _last_days(today, 30, "last_30_days")
    if normalized == "last_90_days":
        return _last_days(today, 90, "last_90_days")
    if normalized == "this_month":
        start = today.replace(day=1)
        return HealthQueryTimeRange(start, today, "this_month", (today - start).days + 1)
    if normalized == "last_month":
        first_this_month = today.replace(day=1)
        end = first_this_month - timedelta(days=1)
        start = end.replace(day=1)
        return HealthQueryTimeRange(start, end, "last_month", (end - start).days + 1)
    return None


def _last_days(today: date, days: int, label: str) -> HealthQueryTimeRange:
    return HealthQueryTimeRange(today - timedelta(days=days - 1), today, label, days)


def _source_type_for_intent(intent: HealthQueryIntent) -> str | None:
    return {
        HealthQueryIntent.QUERY_SYMPTOMS: "symptoms",
        HealthQueryIntent.QUERY_MEDICAL_EVENTS: "medical_events",
        HealthQueryIntent.QUERY_DOCUMENTS: "documents",
        HealthQueryIntent.QUERY_ALERTS: "alerts",
        HealthQueryIntent.QUERY_DAILY_STATUS: "daily_status",
    }.get(intent)


def _tool_input_for_plan(
    intent: HealthQueryIntent,
    time_range: HealthQueryTimeRange,
    metric_type: str | None,
    aggregation: str,
) -> dict[str, Any]:
    if intent == HealthQueryIntent.QUERY_METRICS:
        return {"days": time_range.days, "metric_type": metric_type, "aggregation": aggregation}
    if intent == HealthQueryIntent.QUERY_BLOOD_PRESSURE:
        return {"days": time_range.days}
    if intent in {HealthQueryIntent.QUERY_MEDICAL_EVENTS, HealthQueryIntent.QUERY_ALERTS}:
        return {"days": time_range.days, "limit": 10}
    if intent == HealthQueryIntent.QUERY_DOCUMENTS:
        return {"limit": 10}
    if intent == HealthQueryIntent.QUERY_DAILY_STATUS:
        return {"days": time_range.days, "limit": 10}
    return {"days": time_range.days}


def _coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_excerpt(value: Any, max_length: int) -> str:
    text = str(value or "").strip()
    return text[:max_length]


def _safe_response_summary(response: LLMResponse) -> str:
    return f"provider={response.provider}; model={response.model}; finish_reason={response.finish_reason or 'unknown'}"
