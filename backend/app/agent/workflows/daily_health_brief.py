from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agent.enums import AgentWorkflowName
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult, ToolExecutionRequest, ToolExecutionResult
from app.agent.tool_executor import AgentToolExecutor
from app.agent.tool_registry import AgentToolRegistry
from app.agent.tools import register_readonly_health_tools


DEFAULT_DAYS = 7
DEFAULT_LIMIT = 10
READONLY_HEALTH_BRIEF_TOOLS = (
    "health_profile.get",
    "health_data.blood_pressure.summary",
    "health_record.symptoms.summary",
    "medical_timeline.followups.list",
    "alerts.active.list",
)
PARTIAL_UNAVAILABLE_MESSAGE = "部分信息因权限设置暂不可用。"


class DailyHealthBriefWorkflow:
    workflow_name = AgentWorkflowName.DAILY_HEALTH_BRIEF

    def __init__(self, executor: AgentToolExecutor | None = None) -> None:
        if executor is None:
            registry = register_readonly_health_tools(AgentToolRegistry())
            executor = AgentToolExecutor(registry)
        self.executor = executor

    def run(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
        request = context.request
        results = _BriefToolResults(
            profile=self._call_tool(context, "health_profile.get", {}),
            blood_pressure=self._call_tool(context, "health_data.blood_pressure.summary", {"days": DEFAULT_DAYS}),
            symptoms=self._call_tool(context, "health_record.symptoms.summary", {"days": DEFAULT_DAYS}),
            followups=self._call_tool(context, "medical_timeline.followups.list", {"limit": DEFAULT_LIMIT}),
            alerts=self._call_tool(context, "alerts.active.list", {"limit": DEFAULT_LIMIT}),
        )
        content = build_daily_health_brief_content(results, days=DEFAULT_DAYS)
        return AgentWorkflowResult(
            message="Daily health brief generated from system records.",
            generated_content=content,
            tool_calls_count=len(READONLY_HEALTH_BRIEF_TOOLS),
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
                reason="daily_health_brief",
            ),
        )


@dataclass(frozen=True)
class _BriefToolResults:
    profile: ToolExecutionResult
    blood_pressure: ToolExecutionResult
    symptoms: ToolExecutionResult
    followups: ToolExecutionResult
    alerts: ToolExecutionResult


def build_daily_health_brief_content(results: _BriefToolResults, *, days: int = DEFAULT_DAYS) -> str:
    lines = [
        f"根据系统内记录，已为你整理最近 {days} 天的健康简报：",
        "",
        "1. 健康档案",
        f"- {_profile_line(results.profile)}",
        "",
        "2. 血压记录",
        *[f"- {line}" for line in _blood_pressure_lines(results.blood_pressure)],
        "",
        "3. 症状记录",
        *[f"- {line}" for line in _symptom_lines(results.symptoms)],
        "",
        "4. 复查 / 随访",
        *[f"- {line}" for line in _followup_lines(results.followups)],
        "",
        "5. 提醒",
        *[f"- {line}" for line in _alert_lines(results.alerts)],
        "",
        "说明：",
        "- 本简报只基于系统内已有记录整理，不能替代医生诊断或治疗建议。",
        "- 本简报只做记录整理，不给出用药或处理方案。",
        "- 如有不适或紧急情况，请联系医生或当地急救服务。",
    ]
    return "\n".join(lines)


def _profile_line(result: ToolExecutionResult) -> str:
    if _blocked_or_failed(result):
        return PARTIAL_UNAVAILABLE_MESSAGE
    data = result.output_data or {}
    if data.get("empty") or not data.get("profile"):
        return "系统内暂无相关记录。"
    return "系统内已有基础健康档案记录。"


def _blood_pressure_lines(result: ToolExecutionResult) -> list[str]:
    if _blocked_or_failed(result):
        return [PARTIAL_UNAVAILABLE_MESSAGE]
    summary = ((result.output_data or {}).get("summary") or {})
    count = int(summary.get("count") or 0)
    if count <= 0:
        return ["系统内暂无相关记录。", "本简报不进行医学判断。"]
    latest = summary.get("latest_measured_at")
    lines = [f"系统内共有 {count} 条血压记录。"]
    if latest:
        lines.append(f"最近一次记录时间：{latest}")
    lines.append("本简报不进行医学判断。")
    return lines


def _symptom_lines(result: ToolExecutionResult) -> list[str]:
    if _blocked_or_failed(result):
        return [PARTIAL_UNAVAILABLE_MESSAGE]
    summary = ((result.output_data or {}).get("summary") or {})
    count = int(summary.get("count") or 0)
    if count <= 0:
        return ["系统内暂无相关记录。"]
    lines = [f"系统内共有 {count} 条症状记录。"]
    records = summary.get("records") or []
    latest = records[0] if records else None
    latest_text = _symptom_excerpt(latest)
    if latest_text:
        lines.append(f"最近记录摘要：{latest_text}")
    lines.append("本简报不推断病因。")
    return lines


def _followup_lines(result: ToolExecutionResult) -> list[str]:
    if _blocked_or_failed(result):
        return [PARTIAL_UNAVAILABLE_MESSAGE]
    count = int((result.output_data or {}).get("count") or 0)
    if count <= 0:
        return ["系统内暂无相关记录。"]
    return [f"系统内共有 {count} 条待随访事件。", "本简报不提供治疗建议。"]


def _alert_lines(result: ToolExecutionResult) -> list[str]:
    if _blocked_or_failed(result):
        return [PARTIAL_UNAVAILABLE_MESSAGE]
    count = int((result.output_data or {}).get("count") or 0)
    if count <= 0:
        return ["系统内暂无相关记录。"]
    return [f"系统内共有 {count} 个 active reminders。", "提醒仅表示系统内记录的待办事项。"]


def _symptom_excerpt(record: Any) -> str | None:
    if not isinstance(record, dict):
        return None
    for key in ("symptom_name", "body_part", "severity", "status"):
        value = record.get(key)
        if value:
            return str(value)[:80]
    return None


def _blocked_or_failed(result: ToolExecutionResult) -> bool:
    return result.blocked or result.status != "completed" or result.output_data is None
