from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agent import service as agent_service
from app.agent.enums import AgentSafetyLevel, AgentWorkflowName
from app.agent.langgraph.dispatcher import AgentGraphDispatcher
from app.agent.safety import AgentSafetyPolicy
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult, ToolExecutionRequest, ToolExecutionResult
from app.agent.tool_executor import AgentToolExecutor
from app.agent.tool_registry import AgentToolRegistry
from app.agent.persona import DAILY_BRIEF_PERSONA_GUIDANCE
from app.agent.tools import register_health_query_tools
from app.core.config import Settings, get_settings
from app.llm.client import LLMClient, get_llm_client
from app.llm.errors import LLMConfigurationError, LLMProviderError, LLMTimeoutError
from app.rag.context import safe_rag_context_for_agent


DEFAULT_DAYS = 7
RECENT_DAYS = 2
DEFAULT_LIMIT = 10
READONLY_HEALTH_BRIEF_TOOLS = (
    "health_profile.get",
    "health_data.metrics.recent",
    "health_data.metrics.recent",
    "health_data.blood_pressure.summary",
    "health_data.blood_pressure.summary",
    "health_record.symptoms.summary",
    "medical_timeline.events.query",
    "documents.query",
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
            registry = register_health_query_tools(AgentToolRegistry())
            executor = AgentToolExecutor(registry)
        self.executor = executor
        self.settings = settings
        self.llm_client = llm_client
        self.graph_dispatcher = AgentGraphDispatcher(settings or get_settings())

    def run(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
        from app.agent.langgraph.graphs.daily_health_brief_graph import DailyHealthBriefGraph

        return self.graph_dispatcher.run_or_fallback(
            context,
            self.workflow_name,
            DailyHealthBriefGraph(workflow=self),
            lambda: self._run_without_graph(context),
        )

    def _run_without_graph(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
        results = _BriefToolResults(
            profile=self._call_tool(context, "health_profile.get", {}),
            recent_metrics=self._call_tool(context, "health_data.metrics.recent", {"days": RECENT_DAYS, "limit": DEFAULT_LIMIT}),
            weekly_metrics=self._call_tool(context, "health_data.metrics.recent", {"days": DEFAULT_DAYS, "limit": 50}),
            recent_blood_pressure=self._call_tool(context, "health_data.blood_pressure.summary", {"days": RECENT_DAYS}),
            blood_pressure=self._call_tool(context, "health_data.blood_pressure.summary", {"days": DEFAULT_DAYS}),
            symptoms=self._call_tool(context, "health_record.symptoms.summary", {"days": DEFAULT_DAYS}),
            events=self._call_tool(context, "medical_timeline.events.query", {"days": DEFAULT_DAYS}),
            documents=self._call_tool(context, "documents.query", {"limit": DEFAULT_LIMIT}),
            followups=self._call_tool(context, "medical_timeline.followups.list", {"limit": DEFAULT_LIMIT}),
            alerts=self._call_tool(context, "alerts.active.list", {"limit": DEFAULT_LIMIT}),
        )
        rule_content = build_daily_health_brief_content(results, days=DEFAULT_DAYS)
        rule_content, rag_summary = maybe_append_daily_brief_rag_context(
            context,
            rule_content,
            settings=self.settings,
        )
        llm_attempt = maybe_generate_daily_brief_with_llm(
            results,
            rule_content=rule_content,
            days=DEFAULT_DAYS,
            settings=self.settings,
            llm_client=self.llm_client,
        )
        content = llm_attempt.content
        _record_rag_safety_summary(context, rag_summary)
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
    recent_metrics: ToolExecutionResult
    weekly_metrics: ToolExecutionResult
    recent_blood_pressure: ToolExecutionResult
    blood_pressure: ToolExecutionResult
    symptoms: ToolExecutionResult
    events: ToolExecutionResult
    documents: ToolExecutionResult
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


@dataclass(frozen=True)
class DailyBriefRagSummary:
    rag_used: bool
    rag_source_count: int
    fallback_reason: str | None


def maybe_append_daily_brief_rag_context(
    context: AgentWorkflowContext,
    rule_content: str,
    *,
    settings: Settings | None = None,
) -> tuple[str, DailyBriefRagSummary]:
    result, lines, fallback_reason = safe_rag_context_for_agent(
        context.db,
        current_user_id=context.request.actor_user_id,
        target_user_id=context.request.target_user_id,
        family_id=context.request.family_id,
        query="daily health brief recent system records",
        top_k=5,
        settings=settings,
    )
    # RAG snippets stay internal. They may inform the workflow audit trail, but
    # should never be rendered as user-facing citations or runtime metadata.
    if not lines:
        return rule_content, DailyBriefRagSummary(False, 0, fallback_reason)
    return rule_content, DailyBriefRagSummary(True, len(result.results) if result else len(lines), None)


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

    if not _contains_cjk(content):
        return DailyBriefLLMAttempt(
            content=rule_content,
            llm_used=True,
            llm_attempted=True,
            llm_provider=response.provider,
            llm_model=response.model,
            fallback_used=True,
            fallback_reason="llm_output_not_chinese",
        )

    if not _is_compact_daily_brief(content):
        return DailyBriefLLMAttempt(
            content=rule_content,
            llm_used=True,
            llm_attempted=True,
            llm_provider=response.provider,
            llm_model=response.model,
            fallback_used=True,
            fallback_reason="llm_output_not_compact",
        )

    content = _ensure_daily_brief_boundary(content)
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

    if not _is_structured_home_brief(content):
        return DailyBriefLLMAttempt(
            content=rule_content,
            llm_used=True,
            llm_attempted=True,
            llm_provider=response.provider,
            llm_model=response.model,
            fallback_used=True,
            fallback_reason="llm_output_not_structured",
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
    return _build_daily_brief_llm_prompt_v2(results, days=days)


def _build_daily_brief_llm_prompt_v2(results: _BriefToolResults, *, days: int) -> str:
    fact_package = build_daily_brief_fact_package(results, days=days)
    return "\n".join(
        [
            "请依据下面的安全事实包，写一份首页健康小结，并严格保留以下栏目结构。",
            "第一行必须是“健康小结 🌱”，第二行说明整理的是最近 7 天的已记录信息。",
            "按有数据的栏目依次写“❤️ 身体指标”“😴 生活状态”“🏃 日常习惯”“📌 小提醒”；每个栏目用一到两句，带上真实的记录次数、最近一次或平均值。",
            "如果数据不够，不要补造数值或评价；没有数据的栏目直接省略。血压只能说明已记录次数、最近值、平均值或范围，不要写正常、稳定、波动异常等判断。",
            "小提醒只可复述系统内已有提醒/随访事项，或建议继续积累已有指标记录；不要诊断或给治疗建议。",
            "内容只能整理已给出的事实。不要诊断、确诊、开处方、给剂量、建议停药或替代医生判断。",
            "不要使用 Markdown 星号，不要提及工具、文件路径、原始文本、模型或内部状态。用简体中文。",
            "安全事实包：",
            fact_package,
        ]
    )


def build_daily_brief_fact_package(results: _BriefToolResults, *, days: int = DEFAULT_DAYS) -> str:
    """Create a compact, ToolExecutor-derived fact package for the LLM only."""
    highlights = _brief_candidate_lines(results, days=days)
    return "\n".join(
        [
            "可选健康重点（优先选择两项不同类型的信息表达）：",
            *[f"- {line}" for line in highlights],
        ]
    )


def _brief_candidate_lines(results: _BriefToolResults, *, days: int) -> list[str]:
    """Prefer recent recorded health facts; use BMI only when no recent fact is available."""
    candidates = [
        *_metric_overview_lines(results.recent_metrics, window_label="近48小时"),
        *_blood_pressure_lines(results.recent_blood_pressure, window_label="近48小时"),
        *_metric_overview_lines(results.weekly_metrics, window_label=f"最近{days}天"),
        *_blood_pressure_lines(results.blood_pressure, window_label=f"最近{days}天"),
        *_positive_count_lines(results.followups, label="待随访事项"),
        *_positive_count_lines(results.alerts, label="健康提醒"),
        _bmi_line(results.profile, results.weekly_metrics),
    ]
    meaningful = [line for line in candidates if line and "暂时没有" not in line and line != PARTIAL_UNAVAILABLE_MESSAGE]
    return _unique_lines(meaningful) or ["系统内暂时没有足够的近期健康记录"]


def _distinct_brief_highlights(lines: list[str], *, limit: int = 2) -> list[str]:
    topics = ("睡眠", "血压", "体重", "步数", "心率", "体温", "待随访", "健康提醒", "BMI")
    selected: list[str] = []
    selected_topics: set[str] = set()
    for line in lines:
        topic = next((item for item in topics if item in line), line)
        if topic in selected_topics:
            continue
        selected.append(line)
        selected_topics.add(topic)
        if len(selected) == limit:
            break
    return selected


def _recent_focus_lines(results: _BriefToolResults) -> list[str]:
    lines = _metric_overview_lines(results.recent_metrics, window_label="近48小时")
    lines.extend(_blood_pressure_lines(results.recent_blood_pressure, window_label="近48小时"))
    return _unique_lines(lines) or ["系统内暂时没有近48小时的健康记录"]


def _weekly_overview_lines(results: _BriefToolResults, *, days: int) -> list[str]:
    lines = _metric_overview_lines(results.weekly_metrics, window_label=f"最近{days}天")
    lines.extend(_blood_pressure_lines(results.blood_pressure, window_label=f"最近{days}天"))
    lines.extend(_count_line(results.symptoms, label="症状记录"))
    lines.extend(_count_line(results.events, label="健康事件"))
    return _unique_lines(lines) or [f"系统内暂时没有最近{days}天的相关记录"]


def _care_context_lines(results: _BriefToolResults) -> list[str]:
    lines = [_profile_line(results.profile)]
    lines.extend(_count_line(results.documents, label="医疗资料"))
    lines.extend(_count_line(results.followups, label="待随访事项"))
    lines.extend(_count_line(results.alerts, label="健康提醒"))
    return _unique_lines(lines)


def _metric_overview_lines(result: ToolExecutionResult, *, window_label: str) -> list[str]:
    if _blocked_or_failed(result):
        return [PARTIAL_UNAVAILABLE_MESSAGE]
    data = result.output_data or {}
    summaries = data.get("metric_summaries") if isinstance(data.get("metric_summaries"), list) else []
    if not summaries:
        return []
    lines: list[str] = []
    for summary in summaries:
        if not isinstance(summary, dict):
            continue
        label = _metric_label(summary.get("metric_type"))
        count = int(summary.get("count") or 0)
        latest = _format_metric_value(summary.get("latest_value"), summary.get("unit"))
        average = _format_metric_value(summary.get("avg_value"), summary.get("unit"))
        if count <= 0:
            continue
        detail = f"{window_label}{label}记录 {count} 条"
        if latest:
            detail += f"，最近一次 {latest}"
        if average and average != latest:
            detail += f"，平均约 {average}"
        lines.append(detail)
    return lines


def _blood_pressure_lines(result: ToolExecutionResult, *, window_label: str | None = None) -> list[str]:
    if _blocked_or_failed(result):
        return [PARTIAL_UNAVAILABLE_MESSAGE]
    summary = ((result.output_data or {}).get("summary") or {})
    count = int(summary.get("count") or 0)
    prefix = f"{window_label}" if window_label else "系统内"
    if count <= 0:
        return [f"{prefix}暂时没有血压记录"]
    latest_systolic = summary.get("latest_systolic")
    latest_diastolic = summary.get("latest_diastolic")
    average_systolic = summary.get("avg_systolic")
    average_diastolic = summary.get("avg_diastolic")
    detail = f"{prefix}血压记录 {count} 次"
    if latest_systolic is not None and latest_diastolic is not None:
        detail += f"，最近一次 {latest_systolic}/{latest_diastolic} mmHg"
    if average_systolic is not None and average_diastolic is not None:
        detail += f"，平均约 {_format_number(average_systolic)}/{_format_number(average_diastolic)} mmHg"
    return [detail]


def _count_line(result: ToolExecutionResult, *, label: str) -> list[str]:
    if _blocked_or_failed(result):
        return [f"{label}{PARTIAL_UNAVAILABLE_MESSAGE}"]
    data = result.output_data or {}
    count = int(data.get("count") or ((data.get("summary") or {}).get("count") or 0))
    if count <= 0:
        return [f"系统内暂时没有{label}"]
    return [f"系统内有 {count} 条{label}"]


def _positive_count_lines(result: ToolExecutionResult, *, label: str) -> list[str]:
    if _blocked_or_failed(result):
        return []
    data = result.output_data or {}
    count = int(data.get("count") or ((data.get("summary") or {}).get("count") or 0))
    return [f"当前有 {count} 条{label}"] if count > 0 else []


def _bmi_line(profile_result: ToolExecutionResult, metrics_result: ToolExecutionResult) -> str | None:
    if _blocked_or_failed(profile_result) or _blocked_or_failed(metrics_result):
        return None
    profile = (profile_result.output_data or {}).get("profile") or {}
    height_cm = profile.get("height_cm") if isinstance(profile, dict) else None
    if not isinstance(height_cm, (int, float)) or height_cm <= 0:
        return None
    for summary in (metrics_result.output_data or {}).get("metric_summaries") or []:
        if not isinstance(summary, dict) or summary.get("metric_type") != "weight":
            continue
        weight_kg = summary.get("latest_value")
        if isinstance(weight_kg, (int, float)) and weight_kg > 0:
            bmi = round(float(weight_kg) / ((float(height_cm) / 100) ** 2), 1)
            return f"按最近一次体重 {_format_number(weight_kg)} kg 和身高 {_format_number(height_cm)} cm 计算，BMI 约为 {bmi}"
    return None


def _metric_label(value: Any) -> str:
    return {
        "sleep": "睡眠",
        "sleep_duration": "睡眠",
        "weight": "体重",
        "steps": "步数",
        "heart_rate": "心率",
        "bmi": "BMI",
        "temperature": "体温",
    }.get(str(value or ""), "健康指标")


def _format_metric_value(value: Any, unit: Any) -> str | None:
    if value is None or value == "":
        return None
    return f"{_format_number(value)} {str(unit or '').strip()}".strip()


def _format_number(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(round(value, 1)) if isinstance(value, float) else str(value)


def _unique_lines(lines: list[str]) -> list[str]:
    return list(dict.fromkeys(line for line in lines if line))


def _legacy_build_daily_brief_llm_prompt(results: _BriefToolResults, *, days: int = DEFAULT_DAYS) -> str:
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
    return DAILY_BRIEF_PERSONA_GUIDANCE + "\n\n" + _legacy_daily_brief_system_prompt()


def _legacy_daily_brief_system_prompt() -> str:
    natural_language_rule = (
        "请始终使用简体中文，以自然、温和、简洁的方式整理已有记录。"
        "先给出一句概括，再提供不超过四条易读要点。"
        "不要展示引用、文件路径、工具名称、运行状态、模型信息或任何内部字段。"
    )
    return natural_language_rule + (
        "你不是医生。你只能根据系统内结构化记录整理健康简报，不能替代医生。"
        "不要诊断，不要确诊，不要处方，不要给药物剂量，不要建议停药或换药，"
        "不要判断正常/异常/高风险/低风险，不要做急救判断，"
        "不要承诺自动急救、自动报警或自动联系医院/家人。"
        "无记录时只能说系统内暂无相关记录。"
        "如遇紧急情况，应联系医生或当地急救服务。"
    )


def _contains_cjk(value: str) -> bool:
    return any("\u4e00" <= character <= "\u9fff" for character in value)


def _is_compact_daily_brief(content: str) -> bool:
    """Keep homepage summaries conversational instead of report-shaped."""
    stripped = content.strip()
    if len(stripped) > 180:
        return False
    return not any(marker in stripped for marker in ("\n-", "\n*", "\n1.", "\n2.", "###"))


def _is_structured_home_brief(content: str) -> bool:
    headings = ("❤️ 身体指标", "😴 生活状态", "🏃 日常习惯", "📌 小提醒")
    return content.startswith("健康小结 🌱") and "📌 小提醒" in content and any(heading in content for heading in headings[:-1])


def _ensure_daily_brief_boundary(content: str) -> str:
    has_source = "\u7cfb\u7edf" in content
    has_doctor_boundary = "\u533b\u751f" in content and ("\u5224\u65ad" in content or "\u8bca\u65ad" in content)
    has_urgent_boundary = "\u8054\u7cfb\u533b\u751f" in content or "\u53ca\u65f6\u5c31\u533b" in content
    if has_source and has_doctor_boundary and has_urgent_boundary:
        return content
    boundary = "基于系统内已有记录整理，不替代医生判断；如有明显不适请及时就医。"
    return f"{content.rstrip()}\n\n{boundary}"


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


def _record_rag_safety_summary(context: AgentWorkflowContext, summary: DailyBriefRagSummary) -> None:
    if not summary.rag_used and summary.fallback_reason == "rag_disabled":
        return
    trace = agent_service.get_trace(context.db, context.trace_id)
    if trace is None:
        return
    flags = ["rag_daily_brief"]
    if summary.fallback_reason:
        flags.append(f"fallback:{summary.fallback_reason}")
    agent_service.record_safety_check(
        context.db,
        request_id=trace.request_id,
        workflow_name=trace.workflow_name,
        safety_level=AgentSafetyLevel(context.safety_level),
        passed=summary.fallback_reason not in {"permission_denied"},
        safety_flags=flags,
        blocked_reason="rag_permission_denied" if summary.fallback_reason == "permission_denied" else None,
        input_risk_summary=(
            f"rag_used={str(summary.rag_used).lower()};"
            f"rag_source_count={summary.rag_source_count};"
            f"fallback_reason={summary.fallback_reason or 'none'}"
        ),
        original_answer_summary="rag_raw_sources_omitted",
        revised_answer_summary="safe_rag_citations_only" if summary.rag_used else "rag_fallback",
        was_rewritten=False,
    )


def build_daily_health_brief_content(results: _BriefToolResults, *, days: int = DEFAULT_DAYS) -> str:
    return _build_structured_daily_health_brief(results, days=days)


def _build_structured_daily_health_brief(results: _BriefToolResults, *, days: int) -> str:
    sections: list[str] = []
    body_lines = _body_metric_lines(results)
    if body_lines:
        sections.append("❤️ 身体指标\n" + "\n".join(body_lines))

    lifestyle_lines = _lifestyle_metric_lines(results)
    if lifestyle_lines:
        sections.append("😴 生活状态\n" + "\n".join(lifestyle_lines))

    habit_lines = _habit_metric_lines(results)
    if habit_lines:
        sections.append("🏃 日常习惯\n" + "\n".join(habit_lines))

    reminder_lines = _daily_brief_reminder_lines(results)
    if not reminder_lines:
        tracked = _tracked_metric_labels(results.weekly_metrics)
        if tracked:
            reminder_lines.append(f"继续积累{'、'.join(tracked)}记录，更容易观察个人长期趋势。")
        else:
            reminder_lines.append("目前系统内暂无足够的近期记录；补记一项睡眠、血压或体重后，我可以继续帮你整理。")
    sections.append("📌 小提醒\n" + "\n".join(reminder_lines[:2]))

    availability_note = _brief_availability_note(results)
    return "\n\n".join(
        [
            "健康小结 🌱\n我帮你整理了最近 7 天的已记录信息。",
            *sections,
            *([availability_note] if availability_note else []),
            "基于系统内已有记录整理，不替代医生判断；如有明显不适请及时就医。",
        ]
    )


def _body_metric_lines(results: _BriefToolResults) -> list[str]:
    lines: list[str] = []
    summary = _tool_summary(results.blood_pressure)
    count = _summary_count(summary)
    if count:
        latest = _blood_pressure_value(summary, "latest_systolic", "latest_diastolic")
        average = _blood_pressure_value(summary, "avg_systolic", "avg_diastolic")
        detail = f"最近 7 天记录了 {count} 次血压"
        if latest:
            detail += f"，最近一次为 {latest}"
        if average and average != latest:
            detail += f"，平均约 {average}"
        minimum = _blood_pressure_value(summary, "min_systolic", "min_diastolic")
        maximum = _blood_pressure_value(summary, "max_systolic", "max_diastolic")
        if count > 1 and minimum and maximum and minimum != maximum:
            detail += f"，已记录范围为 {minimum} 至 {maximum}"
        lines.append(detail + "。")
    lines.extend(_metric_lines(results.weekly_metrics, ("weight", "heart_rate", "temperature")))
    return lines


def _lifestyle_metric_lines(results: _BriefToolResults) -> list[str]:
    return _metric_lines(results.weekly_metrics, ("sleep", "sleep_duration"))


def _habit_metric_lines(results: _BriefToolResults) -> list[str]:
    return _metric_lines(results.weekly_metrics, ("steps",))


def _metric_lines(result: ToolExecutionResult, metric_types: tuple[str, ...]) -> list[str]:
    if _blocked_or_failed(result):
        return []
    summaries = (result.output_data or {}).get("metric_summaries") or []
    lines: list[str] = []
    for summary in summaries:
        if not isinstance(summary, dict) or str(summary.get("metric_type")) not in metric_types:
            continue
        count = _summary_count(summary)
        if not count:
            continue
        metric_type = str(summary.get("metric_type"))
        label = _metric_label(metric_type)
        latest = _format_summary_metric_value(summary.get("latest_value"), summary.get("unit"), metric_type)
        average = _format_summary_metric_value(summary.get("avg_value"), summary.get("unit"), metric_type)
        detail = f"最近 7 天记录了 {count} 次{label}"
        if average:
            detail += f"，平均约 {average}"
        if latest and latest != average:
            detail += f"，最近一次为 {latest}"
        lines.append(detail + "。")
    return lines


def _daily_brief_reminder_lines(results: _BriefToolResults) -> list[str]:
    lines: list[str] = []
    if not _blocked_or_failed(results.followups):
        items = (results.followups.output_data or {}).get("items") or []
        if items:
            title = items[0].get("title") if isinstance(items[0], dict) else None
            lines.append(f"系统内有待跟进事项：{str(title or '请查看已有健康事件记录')}。")
    if not _blocked_or_failed(results.alerts):
        items = (results.alerts.output_data or {}).get("items") or []
        if items:
            title = items[0].get("title") if isinstance(items[0], dict) else None
            lines.append(f"当前提醒：{str(title or '请查看已有提醒')}。")
    return lines


def _tracked_metric_labels(result: ToolExecutionResult) -> list[str]:
    if _blocked_or_failed(result):
        return []
    return _unique_lines(
        [_metric_label(summary.get("metric_type")) for summary in (result.output_data or {}).get("metric_summaries") or [] if isinstance(summary, dict)]
    )[:3]


def _tool_summary(result: ToolExecutionResult) -> dict[str, Any]:
    if _blocked_or_failed(result):
        return {}
    summary = (result.output_data or {}).get("summary") or {}
    return summary if isinstance(summary, dict) else {}


def _summary_count(summary: dict[str, Any]) -> int:
    try:
        return int(summary.get("count") or 0)
    except (TypeError, ValueError):
        return 0


def _blood_pressure_value(summary: dict[str, Any], systolic_key: str, diastolic_key: str) -> str | None:
    systolic = summary.get(systolic_key)
    diastolic = summary.get(diastolic_key)
    if systolic is None or diastolic is None:
        return None
    return f"{_format_number(systolic)}/{_format_number(diastolic)} mmHg"


def _format_summary_metric_value(value: Any, unit: Any, metric_type: str) -> str | None:
    if value is None or value == "":
        return None
    if metric_type in {"sleep", "sleep_duration"} and isinstance(value, (int, float)):
        hours = int(float(value))
        minutes = round((float(value) - hours) * 60)
        return f"{hours} 小时" if minutes == 0 else f"{hours} 小时 {minutes} 分钟"
    display_unit = {"bpm": "次/分", "steps": "步"}.get(str(unit or "").lower(), unit)
    return _format_metric_value(value, display_unit)


def _build_daily_health_brief_fallback_v2(results: _BriefToolResults, *, days: int) -> str:
    highlights = _brief_candidate_lines(results, days=days)
    if highlights[0] == "系统内暂时没有足够的近期健康记录":
        body = "系统内暂无相关记录。今天我先在这里替你留着位置；下次补记一项睡眠、体重或血压时，我们就能慢慢看出变化。"
    else:
        body = f"我替你留意到：{'；'.join(_distinct_brief_highlights(highlights))}。这些是近期已记录的信息，我们之后可以继续一起看看变化。"
    availability_note = _brief_availability_note(results)
    return "\n\n".join(
        [
            body,
            *([availability_note] if availability_note else []),
            "基于系统内已有记录整理，不替代医生判断；如有明显不适请及时就医。",
        ]
    )


def _brief_availability_note(results: _BriefToolResults) -> str | None:
    if any(
        result.blocked
        for result in (
            results.profile,
            results.recent_metrics,
            results.weekly_metrics,
            results.recent_blood_pressure,
            results.blood_pressure,
            results.symptoms,
            results.events,
            results.documents,
            results.followups,
            results.alerts,
        )
    ):
        return PARTIAL_UNAVAILABLE_MESSAGE
    return None


def _build_conversational_daily_health_brief_content(results: _BriefToolResults, *, days: int) -> str:
    sections = [
        f"• 健康档案：{_profile_line(results.profile)}",
        f"• 血压记录：{'；'.join(_blood_pressure_lines(results.blood_pressure))}",
        f"• 症状记录：{'；'.join(_symptom_lines(results.symptoms))}",
        f"• 复查与随访：{'；'.join(_followup_lines(results.followups))}",
        f"• 提醒：{'；'.join(_alert_lines(results.alerts))}",
    ]
    boundary = (
        "这份小结仅根据系统内已有记录整理，不替代医生判断。"
        "如有明显不适或紧急情况，请联系医生或当地急救服务。"
    )
    return "\n\n".join(
        [
            f"根据系统内记录，我把最近 {days} 天的信息整理成一份健康简报：",
            "\n".join(sections),
            boundary,
        ]
    )


def _build_legacy_daily_health_brief_content(results: _BriefToolResults, *, days: int = DEFAULT_DAYS) -> str:
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


def _legacy_blood_pressure_lines(result: ToolExecutionResult) -> list[str]:
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
