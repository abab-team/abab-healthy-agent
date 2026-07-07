from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agent import service as agent_service
from app.agent.enums import AgentSafetyLevel, AgentWorkflowName
from app.agent.safety import AgentSafetyPolicy
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult, ToolExecutionRequest, ToolExecutionResult
from app.agent.tool_executor import AgentToolExecutor
from app.agent.tool_registry import AgentToolRegistry
from app.agent.tools import register_readonly_health_tools
from app.core.config import Settings, get_settings
from app.llm.client import LLMClient, get_llm_client
from app.llm.errors import LLMConfigurationError, LLMProviderError, LLMTimeoutError


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
LLM_DAILY_BRIEF_BLOCKED_TERMS = (
    "诊断结果",
    "诊断是",
    "诊断为",
    "确诊",
    "处方",
    "剂量",
    "停药",
    "自动报警",
    "自动联系医院",
    "自动联系家人",
    "高风险",
    "低风险",
    "正常",
    "异常",
    "no need to see a doctor",
    "nothing is wrong",
    "prescription",
    "dosage",
    "stop medication",
    "high risk",
    "low risk",
)


class DailyHealthBriefWorkflow:
    workflow_name = AgentWorkflowName.DAILY_HEALTH_BRIEF

    def __init__(
        self,
        executor: AgentToolExecutor | None = None,
        *,
        settings: Settings | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        if executor is None:
            registry = register_readonly_health_tools(AgentToolRegistry())
            executor = AgentToolExecutor(registry)
        self.executor = executor
        self.settings = settings
        self.llm_client = llm_client

    def run(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
        request = context.request
        results = _BriefToolResults(
            profile=self._call_tool(context, "health_profile.get", {}),
            blood_pressure=self._call_tool(context, "health_data.blood_pressure.summary", {"days": DEFAULT_DAYS}),
            symptoms=self._call_tool(context, "health_record.symptoms.summary", {"days": DEFAULT_DAYS}),
            followups=self._call_tool(context, "medical_timeline.followups.list", {"limit": DEFAULT_LIMIT}),
            alerts=self._call_tool(context, "alerts.active.list", {"limit": DEFAULT_LIMIT}),
        )
        rule_content = build_daily_health_brief_content(results, days=DEFAULT_DAYS)
        llm_attempt = maybe_generate_daily_brief_with_llm(
            results,
            rule_content=rule_content,
            days=DEFAULT_DAYS,
            settings=self.settings,
            llm_client=self.llm_client,
        )
        content = llm_attempt.content
        _record_llm_safety_summary(context, llm_attempt)
        return AgentWorkflowResult(
            message=llm_attempt.message,
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


@dataclass(frozen=True)
class DailyBriefLLMAttempt:
    content: str
    llm_used: bool
    llm_attempted: bool
    llm_provider: str | None
    llm_model: str | None
    fallback_used: bool
    fallback_reason: str | None
    safety_filtered: bool = False

    @property
    def message(self) -> str:
        return (
            "Daily health brief generated from system records. "
            f"llm_used={str(self.llm_used).lower()}; "
            f"llm_provider={self.llm_provider or 'none'}; "
            f"llm_model={self.llm_model or 'none'}; "
            f"fallback_used={str(self.fallback_used).lower()}; "
            f"fallback_reason={self.fallback_reason or 'none'}; "
            f"safety_filtered={str(self.safety_filtered).lower()}"
        )


def maybe_generate_daily_brief_with_llm(
    results: _BriefToolResults,
    *,
    rule_content: str,
    days: int = DEFAULT_DAYS,
    settings: Settings | None = None,
    llm_client: LLMClient | None = None,
) -> DailyBriefLLMAttempt:
    effective_settings = settings or get_settings()
    if not effective_settings.LLM_ENABLED:
        return _fallback(rule_content, "llm_disabled")
    if not effective_settings.DAILY_BRIEF_USE_LLM:
        return _fallback(rule_content, "daily_brief_use_llm_disabled")

    client = llm_client
    try:
        client = client or get_llm_client(effective_settings)
        response = client.generate_text(
            system_prompt=_daily_brief_system_prompt(),
            user_prompt=build_daily_brief_llm_prompt(results, days=days),
            temperature=effective_settings.LLM_TEMPERATURE,
            max_tokens=effective_settings.LLM_MAX_TOKENS,
            metadata={"workflow_type": "daily_health_brief"},
        )
    except LLMTimeoutError:
        return _fallback(rule_content, "llm_timeout", attempted=True)
    except LLMConfigurationError:
        return _fallback(rule_content, "llm_configuration_error", attempted=True)
    except LLMProviderError:
        return _fallback(rule_content, "llm_provider_error", attempted=True)
    except Exception:
        return _fallback(rule_content, "llm_error", attempted=True)

    if not _is_valid_llm_response(response):
        return _fallback(rule_content, "llm_response_invalid", attempted=True)

    content = response.content.strip()
    if not content:
        return DailyBriefLLMAttempt(
            content=rule_content,
            llm_used=True,
            llm_attempted=True,
            llm_provider=response.provider,
            llm_model=response.model,
            fallback_used=True,
            fallback_reason="empty_llm_output",
        )

    decision = AgentSafetyPolicy().evaluate_output(content, "daily_health_brief")
    if decision.blocked or _contains_blocked_llm_brief_terms(content):
        return DailyBriefLLMAttempt(
            content=rule_content,
            llm_used=True,
            llm_attempted=True,
            llm_provider=response.provider,
            llm_model=response.model,
            fallback_used=True,
            fallback_reason="llm_output_safety_blocked",
            safety_filtered=True,
        )

    return DailyBriefLLMAttempt(
        content=content,
        llm_used=True,
        llm_attempted=True,
        llm_provider=response.provider,
        llm_model=response.model,
        fallback_used=False,
        fallback_reason=None,
    )


def build_daily_brief_llm_prompt(results: _BriefToolResults, *, days: int = DEFAULT_DAYS) -> str:
    lines = [
        f"请根据以下系统内结构化摘要生成最近 {days} 天健康简报。",
        "只能整理记录，不能诊断、不能处方、不能给剂量、不能建议停药、不能判断急救。",
        "",
        "结构化摘要：",
        f"- 健康档案：{_profile_line(results.profile)}",
        f"- 血压记录：{'；'.join(_blood_pressure_lines(results.blood_pressure))}",
        f"- 症状记录：{'；'.join(_symptom_lines(results.symptoms))}",
        f"- 复查 / 随访：{'；'.join(_followup_lines(results.followups))}",
        f"- 提醒：{'；'.join(_alert_lines(results.alerts))}",
        "",
        "输出必须包含：根据系统内记录、系统内、不能替代医生诊断、请联系医生。",
    ]
    return "\n".join(lines)


def _daily_brief_system_prompt() -> str:
    return (
        "你不是医生。你只能根据系统内结构化记录整理健康简报，不能替代医生。"
        "不要诊断，不要确诊，不要处方，不要给药物剂量，不要建议停药或换药，"
        "不要判断正常/异常/高风险/低风险，不要做急救判断，"
        "不要承诺自动急救、自动报警或自动联系医院/家人。"
        "无记录时只能说系统内暂无相关记录。"
        "如遇紧急情况，应联系医生或当地急救服务。"
    )


def _fallback(rule_content: str, reason: str, *, attempted: bool = False) -> DailyBriefLLMAttempt:
    return DailyBriefLLMAttempt(
        content=rule_content,
        llm_used=False,
        llm_attempted=attempted,
        llm_provider=None,
        llm_model=None,
        fallback_used=True,
        fallback_reason=reason,
    )


def _contains_blocked_llm_brief_terms(content: str) -> bool:
    lowered = content.lower()
    return any(term in content or term in lowered for term in LLM_DAILY_BRIEF_BLOCKED_TERMS)


def _is_valid_llm_response(response: Any) -> bool:
    return (
        isinstance(getattr(response, "content", None), str)
        and isinstance(getattr(response, "provider", None), str)
        and isinstance(getattr(response, "model", None), str)
    )


def _record_llm_safety_summary(context: AgentWorkflowContext, attempt: DailyBriefLLMAttempt) -> None:
    if not attempt.llm_attempted:
        return
    trace = agent_service.get_trace(context.db, context.trace_id)
    if trace is None:
        return
    flags = ["llm_daily_brief"]
    if attempt.fallback_used:
        flags.append(f"fallback:{attempt.fallback_reason or 'unknown'}")
    if attempt.safety_filtered:
        flags.append("llm_output_safety_filtered")
    agent_service.record_safety_check(
        context.db,
        request_id=trace.request_id,
        workflow_name=trace.workflow_name,
        safety_level=AgentSafetyLevel(context.safety_level),
        passed=not attempt.safety_filtered,
        safety_flags=flags,
        blocked_reason="llm_output_safety_blocked" if attempt.safety_filtered else None,
        input_risk_summary=(
            f"llm_used={str(attempt.llm_used).lower()};"
            f"fallback_used={str(attempt.fallback_used).lower()};"
            f"fallback_reason={attempt.fallback_reason or 'none'}"
        ),
        original_answer_summary="llm_output_omitted" if attempt.safety_filtered else None,
        revised_answer_summary="rule_brief_fallback" if attempt.fallback_used else "llm_brief_returned",
        was_rewritten=attempt.safety_filtered,
    )


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
