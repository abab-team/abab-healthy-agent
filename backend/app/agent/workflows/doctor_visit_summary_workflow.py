from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agent.enums import AgentWorkflowName
from app.agent.langgraph.dispatcher import AgentGraphDispatcher
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult, ToolExecutionRequest, ToolExecutionResult
from app.agent.tool_executor import AgentToolExecutor
from app.agent.tool_registry import AgentToolRegistry
from app.agent.tools import register_health_query_tools
from app.core.config import get_settings


DEFAULT_DAYS = 30
DEFAULT_LIMIT = 10
WORKFLOW_TYPE = "doctor_visit_summary_workflow"
DOCTOR_SUMMARY_TOOLS = (
    "health_data.blood_pressure.summary",
    "health_record.symptoms.query",
    "medical_timeline.events.query",
    "documents.query",
    "alerts.query",
)
PARTIAL_UNAVAILABLE_MESSAGE = "Some information is unavailable because of permissions or missing system records."


class DoctorVisitSummaryWorkflow:
    workflow_name = AgentWorkflowName.DOCTOR_VISIT_SUMMARY_WORKFLOW

    def __init__(self, executor: AgentToolExecutor | None = None, *, settings=None) -> None:
        if executor is None:
            registry = register_health_query_tools(AgentToolRegistry())
            executor = AgentToolExecutor(registry)
        self.executor = executor
        self.settings = settings or get_settings()
        self.graph_dispatcher = AgentGraphDispatcher(self.settings)

    def run(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
        from app.agent.langgraph.graphs.doctor_visit_summary_graph import DoctorVisitSummaryGraph

        return self.graph_dispatcher.run_or_fallback(
            context,
            self.workflow_name,
            DoctorVisitSummaryGraph(workflow=self),
            lambda: self._run_without_graph(context),
        )

    def _run_without_graph(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
        options = _workflow_options(context)
        results = _DoctorVisitToolResults(
            blood_pressure=self._call_tool(context, "health_data.blood_pressure.summary", {"days": options.days}),
            symptoms=self._call_tool(context, "health_record.symptoms.query", {"days": options.days}),
            events=self._call_tool(context, "medical_timeline.events.query", {"days": options.days}),
            documents=self._call_tool(context, "documents.query", {"limit": options.limit}),
            alerts=self._call_tool(context, "alerts.query", {"limit": options.limit}),
        )
        content = build_doctor_visit_summary_content(results, days=options.days)
        return AgentWorkflowResult(
            message="Doctor visit preparation package generated from system records.",
            generated_content=content,
            tool_calls_count=len(DOCTOR_SUMMARY_TOOLS),
        )

    def _call_tool(self, context: AgentWorkflowContext, tool_name: str, input_data: dict[str, Any]) -> ToolExecutionResult:
        request = context.request
        return self.executor.execute(
            context.db,
            ToolExecutionRequest(
                trace_id=context.trace_id,
                tool_name=tool_name,
                actor_user_id=request.actor_user_id,
                target_user_id=request.target_user_id,
                family_id=request.family_id,
                input_data=input_data,
                confirmed=False,
                safety_level=context.safety_level,
                reason=WORKFLOW_TYPE,
            ),
        )


@dataclass(frozen=True)
class _DoctorVisitOptions:
    days: int
    limit: int


@dataclass(frozen=True)
class _DoctorVisitToolResults:
    blood_pressure: ToolExecutionResult
    symptoms: ToolExecutionResult
    events: ToolExecutionResult
    documents: ToolExecutionResult
    alerts: ToolExecutionResult


def build_doctor_visit_summary_content(results: _DoctorVisitToolResults, *, days: int = DEFAULT_DAYS) -> str:
    lines = [
        f"Based on system records only, here is a doctor visit preparation package for the last {days} days.",
        "This package is for organizing records and questions. It does not replace a doctor's judgment.",
        "",
        "1. Blood pressure records",
        *[f"- {line}" for line in _blood_pressure_lines(results.blood_pressure)],
        "",
        "2. Symptom records",
        *[f"- {line}" for line in _symptom_lines(results.symptoms)],
        "",
        "3. Timeline events",
        *[f"- {line}" for line in _event_lines(results.events)],
        "",
        "4. Document metadata",
        *[f"- {line}" for line in _document_lines(results.documents)],
        "",
        "5. Reminders",
        *[f"- {line}" for line in _alert_lines(results.alerts)],
        "",
        "Questions to discuss with a clinician",
        "- Which system records should I bring or clarify?",
        "- Are there specific follow-up records the clinician wants me to keep?",
        "- Are any uploaded document summaries incomplete and worth reviewing together?",
        "",
        "Safety note: this package only organizes system records. If there is urgent discomfort, contact a clinician or local emergency service.",
    ]
    return "\n".join(lines)


def _workflow_options(context: AgentWorkflowContext) -> _DoctorVisitOptions:
    payload = context.request.workflow_payload or {}
    return _DoctorVisitOptions(
        days=_bounded_int(payload.get("days", DEFAULT_DAYS), field_name="days", minimum=1, maximum=365),
        limit=_bounded_int(payload.get("limit", DEFAULT_LIMIT), field_name="limit", minimum=1, maximum=50),
    )


def _blood_pressure_lines(result: ToolExecutionResult) -> list[str]:
    if _blocked_or_failed(result):
        return [PARTIAL_UNAVAILABLE_MESSAGE]
    summary = ((result.output_data or {}).get("summary") or {})
    count = int(summary.get("count") or 0)
    if count <= 0:
        return ["No related system records are available for this period."]
    latest = summary.get("latest_measured_at")
    lines = [f"{count} stored blood pressure records were found."]
    if latest:
        lines.append(f"Latest recorded time: {latest}.")
    lines.append("No medical judgment is made from these values.")
    return lines


def _symptom_lines(result: ToolExecutionResult) -> list[str]:
    if _blocked_or_failed(result):
        return [PARTIAL_UNAVAILABLE_MESSAGE]
    summary = ((result.output_data or {}).get("summary") or {})
    count = int(summary.get("count") or 0)
    if count <= 0:
        return ["No related system records are available for this period."]
    lines = [f"{count} stored symptom records were found."]
    records = summary.get("records") or []
    latest = _safe_first_record_label(records)
    if latest:
        lines.append(f"Latest safe label: {latest}.")
    lines.append("No cause is inferred from these records.")
    return lines


def _event_lines(result: ToolExecutionResult) -> list[str]:
    if _blocked_or_failed(result):
        return [PARTIAL_UNAVAILABLE_MESSAGE]
    data = result.output_data or {}
    count = int(data.get("count") or 0)
    if count <= 0:
        return ["No related system records are available for this period."]
    follow_up_count = int(data.get("follow_up_needed_count") or 0)
    return [
        f"{count} stored timeline events were found.",
        f"{follow_up_count} events are marked in the system as needing follow-up.",
        "No care plan is generated from these records.",
    ]


def _document_lines(result: ToolExecutionResult) -> list[str]:
    if _blocked_or_failed(result):
        return [PARTIAL_UNAVAILABLE_MESSAGE]
    data = result.output_data or {}
    count = int(data.get("count") or 0)
    if count <= 0:
        return ["No related document metadata is available."]
    return [
        f"{count} document metadata items are available.",
        "File paths, raw OCR, and full extracted text are omitted.",
    ]


def _alert_lines(result: ToolExecutionResult) -> list[str]:
    if _blocked_or_failed(result):
        return [PARTIAL_UNAVAILABLE_MESSAGE]
    data = result.output_data or {}
    count = int(data.get("count") or 0)
    active_count = int(data.get("active_count") or 0)
    if count <= 0:
        return ["No related reminder records are available."]
    return [
        f"{count} reminder records were found.",
        f"{active_count} reminders are currently active in system records.",
        "Reminders are not an emergency service.",
    ]


def _safe_first_record_label(records: Any) -> str | None:
    if not isinstance(records, list) or not records:
        return None
    first = records[0]
    if not isinstance(first, dict):
        return None
    for key in ("symptom_name", "body_part", "status"):
        value = first.get(key)
        if value:
            return str(value)[:80]
    return None


def _bounded_int(value: Any, *, field_name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if number < minimum or number > maximum:
        raise ValueError(f"{field_name} must be between {minimum} and {maximum}")
    return number


def _blocked_or_failed(result: ToolExecutionResult) -> bool:
    return result.blocked or result.status != "completed" or result.output_data is None
