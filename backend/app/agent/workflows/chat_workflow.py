from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agent import service as agent_service
from app.agent.answer_composer import LLMAnswerComposer
from app.agent.chat import HealthQueryIntent, HealthQueryPlan, parse_health_query
from app.agent.critic import AnswerCriticService, CriticReviewRequest, ToolResultSummary
from app.agent.enums import AgentSafetyLevel, AgentWorkflowName
from app.agent.langgraph.adapter import LangGraphExecutionAdapter
from app.agent.memory import service as memory_service
from app.agent.planner import LLMPlannerService
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult, ToolExecutionRequest, ToolExecutionResult
from app.agent.tool_executor import AgentToolExecutor
from app.agent.tool_registry import AgentToolRegistry
from app.agent.tools import register_health_query_tools
from app.core.config import get_settings


SAFE_UNKNOWN_QUERY_MESSAGE = (
    "我现在可以根据系统内记录回答指标、血压、症状、健康事件、文档和提醒相关问题。"
    "请尽量说明要查询的成员和时间范围。"
)
SYSTEM_RECORD_NOTE = "以下内容仅根据系统内记录整理，不用于医疗判断。"
NO_RECORD_NOTE = "这只表示当前系统内没有相关记录，不代表现实中没有相关情况。"
SAFETY_FOOTER = "如有明显不适或紧急情况，请联系医生或当地急救服务。"
PARTIAL_UNAVAILABLE_MESSAGE = "部分信息因权限设置暂不可用。"


class ChatHealthQueryWorkflow:
    workflow_name = AgentWorkflowName.CHAT_WORKFLOW

    def __init__(
        self,
        executor: AgentToolExecutor | None = None,
        *,
        settings=None,
        graph_adapter: LangGraphExecutionAdapter | None = None,
        planner_service: LLMPlannerService | None = None,
        answer_composer: LLMAnswerComposer | None = None,
        critic_service: AnswerCriticService | None = None,
    ) -> None:
        if executor is None:
            executor = AgentToolExecutor(register_health_query_tools(AgentToolRegistry()))
        self.executor = executor
        self.settings = settings or get_settings()
        self.graph_adapter = graph_adapter or LangGraphExecutionAdapter(self.settings)
        self.planner_service = planner_service or LLMPlannerService(settings=self.settings)
        self.answer_composer = answer_composer or LLMAnswerComposer(settings=self.settings)
        self.critic_service = critic_service or AnswerCriticService(settings=self.settings)

    def run(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
        result = self.graph_adapter.run_chat_health_query(
            context,
            lambda: run_chat_health_query(
                context,
                executor=self.executor,
                settings=self.settings,
                planner_service=self.planner_service,
                answer_composer=self.answer_composer,
                critic_service=self.critic_service,
            ),
        )
        return AgentWorkflowResult(
            message=result.answer,
            generated_content=result.answer,
            tool_calls_count=result.tool_calls_count,
        )


@dataclass(frozen=True)
class ChatHealthQueryExecution:
    plan: HealthQueryPlan
    answer: str
    tool_calls_count: int
    graph_node_summary: list[str] | None = None


def run_chat_health_query(
    context: AgentWorkflowContext,
    *,
    executor: AgentToolExecutor,
    settings=None,
    planner_service: LLMPlannerService | None = None,
    answer_composer: LLMAnswerComposer | None = None,
    critic_service: AnswerCriticService | None = None,
) -> ChatHealthQueryExecution:
    memory_context = memory_service.load_session_context(
        context.db,
        user_id=context.request.actor_user_id,
        session_id=context.request.session_id,
    )
    plan = parse_health_query(context.request.user_message)
    plan = memory_service.apply_session_context(context.request.user_message, plan, memory_context)
    if plan.is_unknown and (settings or get_settings()).LLM_PLANNER_ENABLED:
        planner = planner_service or LLMPlannerService(settings=settings or get_settings())
        planner_result = planner.plan(
            user_message=context.request.user_message,
            recent_session_context_summary=memory_context.summary_lines,
            safe_memory_summary=(),
        )
        plan = planner_result.plan
    if plan.is_unknown or not plan.tool_name:
        answer = "\n".join([_unknown_or_clarification_message(plan), SYSTEM_RECORD_NOTE, SAFETY_FOOTER])
        answer = _review_answer(
            context,
            critic_service,
            plan=plan,
            answer=answer,
            safe_tool_result_summary="[]",
            tool_result_summaries=(),
        )
        _record_session_messages(context, plan, answer)
        return ChatHealthQueryExecution(plan=plan, answer=answer, tool_calls_count=0)

    if plan.intent == HealthQueryIntent.QUERY_DAILY_STATUS:
        results = [
            _execute_tool(context, executor, "health_data.metrics.recent", {"days": plan.time_range.days, "limit": 10}),
            _execute_tool(context, executor, "health_record.symptoms.query", {"days": plan.time_range.days}),
            _execute_tool(context, executor, "alerts.query", {"days": plan.time_range.days, "limit": 10}),
        ]
        answer = _compose_daily_status_answer(plan, results)
        answer = _maybe_compose_answer(
            answer_composer,
            plan=plan,
            fallback_answer=answer,
            safe_tool_result_summary=_safe_result_summary(results),
            user_question_excerpt=context.request.user_message,
        )
        answer = _review_answer(
            context,
            critic_service,
            plan=plan,
            answer=answer,
            safe_tool_result_summary=_safe_result_summary(results),
            tool_result_summaries=_tool_result_summaries(results),
        )
        _record_session_messages(context, plan, answer)
        return ChatHealthQueryExecution(plan=plan, answer=answer, tool_calls_count=len(results))

    result = _execute_tool(context, executor, plan.tool_name, dict(plan.tool_input or {}))
    answer = _compose_single_tool_answer(plan, result)
    answer = _maybe_compose_answer(
        answer_composer,
        plan=plan,
        fallback_answer=answer,
        safe_tool_result_summary=_safe_result_summary([result]),
        user_question_excerpt=context.request.user_message,
    )
    answer = _review_answer(
        context,
        critic_service,
        plan=plan,
        answer=answer,
        safe_tool_result_summary=_safe_result_summary([result]),
        tool_result_summaries=_tool_result_summaries([result]),
    )
    _record_session_messages(context, plan, answer)
    return ChatHealthQueryExecution(plan=plan, answer=answer, tool_calls_count=1)


def _record_session_messages(context: AgentWorkflowContext, plan: HealthQueryPlan, answer: str) -> None:
    if not context.request.session_id:
        return
    memory_service.append_message(
        context.db,
        session_id=context.request.session_id,
        role="user",
        content=context.request.user_message,
        intent=plan.intent.value,
        target_user_id=context.request.target_user_id,
        member_label=plan.member_label,
        member_scope=plan.member_scope,
        metric_type=plan.metric_type,
        time_range_label=plan.time_range.label,
        time_range_days=plan.time_range.days,
        tool_name=plan.tool_name,
    )
    memory_service.append_message(
        context.db,
        session_id=context.request.session_id,
        role="assistant",
        content=answer,
        intent=plan.intent.value,
        target_user_id=context.request.target_user_id,
        member_label=plan.member_label,
        member_scope=plan.member_scope,
        metric_type=plan.metric_type,
        time_range_label=plan.time_range.label,
        time_range_days=plan.time_range.days,
        tool_name=plan.tool_name,
    )
    memory_service.create_safe_preference_memory(
        context.db,
        user_id=context.request.actor_user_id,
        family_id=context.request.family_id,
        message=context.request.user_message,
    )


def _unknown_or_clarification_message(plan: HealthQueryPlan) -> str:
    if plan.needs_clarification and plan.clarification_question:
        return plan.clarification_question
    return SAFE_UNKNOWN_QUERY_MESSAGE


def _execute_tool(
    context: AgentWorkflowContext,
    executor: AgentToolExecutor,
    tool_name: str,
    input_data: dict[str, Any],
) -> ToolExecutionResult:
    request = context.request
    return executor.execute(
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
            reason="chat_health_query",
        ),
    )


def _maybe_compose_answer(
    answer_composer: LLMAnswerComposer | None,
    *,
    plan: HealthQueryPlan,
    fallback_answer: str,
    safe_tool_result_summary: str,
    user_question_excerpt: str,
) -> str:
    if answer_composer is None:
        return fallback_answer
    result = answer_composer.compose(
        safe_tool_result_summary=safe_tool_result_summary,
        coverage_note=f"system_records_only; range={plan.time_range.label}; days={plan.time_range.days}",
        user_question_excerpt=user_question_excerpt,
        fallback_answer=fallback_answer,
    )
    return result.answer


def _review_answer(
    context: AgentWorkflowContext,
    critic_service: AnswerCriticService | None,
    *,
    plan: HealthQueryPlan,
    answer: str,
    safe_tool_result_summary: str,
    tool_result_summaries: tuple[ToolResultSummary, ...],
) -> str:
    critic = critic_service or AnswerCriticService(settings=get_settings())
    review = critic.review(
        CriticReviewRequest(
            workflow_type=AgentWorkflowName.CHAT_WORKFLOW.value,
            user_question_excerpt=context.request.user_message[:300],
            draft_answer=answer,
            safe_tool_result_summary=safe_tool_result_summary,
            tool_result_summaries=tool_result_summaries,
            plan_intent=plan.intent.value,
            time_range_label=plan.time_range.label,
        )
    )
    trace = agent_service.get_trace(context.db, context.trace_id)
    if trace is not None:
        agent_service.record_safety_check(
            context.db,
            request_id=trace.request_id,
            workflow_name=AgentWorkflowName.CHAT_WORKFLOW,
            safety_level=AgentSafetyLevel.SAFE if review.passed else AgentSafetyLevel.BLOCKED,
            passed=review.passed,
            intent="critic_review",
            safety_flags=(review.risk_flags + review.grounding_flags)[:20],
            blocked_reason=None if review.passed else review.summary[:300],
            input_risk_summary=f"critic:{review.critic_source}",
            original_answer_summary=answer[:200],
            revised_answer_summary=(review.safe_rewrite or "")[:200] or None,
            was_rewritten=review.rewrite_required,
        )
    if review.rewrite_required and review.safe_rewrite:
        return review.safe_rewrite
    return answer


def _safe_result_summary(results: list[ToolExecutionResult]) -> str:
    parts = []
    for result in results:
        data = result.output_data or {}
        parts.append(
            {
                "tool": result.tool_name,
                "status": result.status,
                "blocked": result.blocked,
                "record_scope": "system_records_only",
                "count": data.get("count") or (data.get("summary") or {}).get("count"),
                "coverage_note": data.get("coverage_note"),
            }
        )
    return str(parts)[:1200]


def _tool_result_summaries(results: list[ToolExecutionResult]) -> tuple[ToolResultSummary, ...]:
    summaries: list[ToolResultSummary] = []
    for result in results:
        data = result.output_data or {}
        count = data.get("count") or (data.get("summary") or {}).get("count")
        summaries.append(
            ToolResultSummary(
                tool_name=result.tool_name,
                status=result.status,
                blocked=result.blocked,
                count=int(count) if isinstance(count, int) or (isinstance(count, str) and count.isdigit()) else None,
                coverage_note=data.get("coverage_note"),
            )
        )
    return tuple(summaries)


def _compose_single_tool_answer(plan: HealthQueryPlan, result: ToolExecutionResult) -> str:
    member = _member_phrase(plan)
    prefix = f"根据系统内记录，{member}{_range_phrase(plan)}的查询结果如下："
    if result.blocked or result.status != "completed":
        return "\n".join([prefix, PARTIAL_UNAVAILABLE_MESSAGE, SYSTEM_RECORD_NOTE, SAFETY_FOOTER])

    data = result.output_data or {}
    if plan.intent == HealthQueryIntent.QUERY_BLOOD_PRESSURE:
        lines = _blood_pressure_lines(data)
    elif plan.intent == HealthQueryIntent.QUERY_METRICS:
        lines = _metric_lines(plan, data)
    elif plan.intent == HealthQueryIntent.QUERY_SYMPTOMS:
        lines = _symptom_lines(data)
    elif plan.intent == HealthQueryIntent.QUERY_MEDICAL_EVENTS:
        lines = _event_lines(data)
    elif plan.intent == HealthQueryIntent.QUERY_DOCUMENTS:
        lines = _document_lines(data)
    elif plan.intent == HealthQueryIntent.QUERY_ALERTS:
        lines = _alert_lines(data)
    else:
        lines = [SAFE_UNKNOWN_QUERY_MESSAGE]
    return "\n".join([prefix, *lines, SYSTEM_RECORD_NOTE, SAFETY_FOOTER])


def _compose_daily_status_answer(plan: HealthQueryPlan, results: list[ToolExecutionResult]) -> str:
    member = _member_phrase(plan)
    lines = [f"根据系统内记录，{member}{_range_phrase(plan)}的健康记录概览如下："]
    for result in results:
        if result.blocked or result.status != "completed":
            lines.append(f"- {PARTIAL_UNAVAILABLE_MESSAGE}")
            continue
        data = result.output_data or {}
        count = int(data.get("count") or ((data.get("summary") or {}).get("count") or 0))
        if count <= 0:
            lines.append(f"- {data.get('coverage_note') or '系统内暂无相关记录。'} {NO_RECORD_NOTE}")
        else:
            lines.append(f"- 系统内找到 {count} 条相关记录；{data.get('coverage_note') or '仅统计已记录数据。'}")
    lines.extend([SYSTEM_RECORD_NOTE, SAFETY_FOOTER])
    return "\n".join(lines)


def _metric_lines(plan: HealthQueryPlan, data: dict[str, Any]) -> list[str]:
    summary = data.get("summary") or {}
    count = int(summary.get("count") or 0)
    metric = plan.metric_type or summary.get("metric_type") or "metric"
    if count <= 0:
        return [f"- 系统内暂无 {metric} 相关记录。", f"- {NO_RECORD_NOTE}"]
    lines = [f"- 系统内共有 {count} 条 {metric} 记录。"]
    if plan.aggregation == "avg" and summary.get("avg_value") is not None:
        lines.append(f"- 已记录数据的平均值：{summary.get('avg_value')} {summary.get('unit') or ''}".strip())
    elif summary.get("latest_value") is not None:
        lines.append(f"- 最近一次已记录值：{summary.get('latest_value')} {summary.get('unit') or ''}".strip())
    lines.append(f"- {data.get('coverage_note') or '仅基于系统内已记录数据。'}")
    return lines


def _blood_pressure_lines(data: dict[str, Any]) -> list[str]:
    summary = data.get("summary") or {}
    count = int(summary.get("count") or 0)
    if count <= 0:
        return ["- 系统内暂无血压相关记录。", f"- {NO_RECORD_NOTE}"]
    lines = [f"- 系统内共有 {count} 条血压记录。"]
    if summary.get("latest_measured_at"):
        lines.append(f"- 最近一次记录时间：{summary.get('latest_measured_at')}")
    lines.append("- 本回答只整理记录数值，不做医学判断。")
    return lines


def _symptom_lines(data: dict[str, Any]) -> list[str]:
    summary = data.get("summary") or {}
    count = int(summary.get("count") or 0)
    if count <= 0:
        return ["- 系统内暂无症状相关记录。", f"- {NO_RECORD_NOTE}"]
    lines = [f"- 系统内共有 {count} 条症状记录。"]
    common = summary.get("common_symptoms") or []
    if common:
        first = common[0]
        lines.append(f"- 出现次数较多的记录标签：{first.get('symptom_name')}，记录 {first.get('count')} 次。")
    lines.append("- 本回答不推断原因。")
    return lines


def _event_lines(data: dict[str, Any]) -> list[str]:
    count = int(data.get("count") or 0)
    if count <= 0:
        return ["- 系统内暂无健康事件相关记录。", f"- {NO_RECORD_NOTE}"]
    return [f"- 系统内共有 {count} 条健康事件记录。", f"- 其中待随访标记 {data.get('follow_up_needed_count') or 0} 条。"]


def _document_lines(data: dict[str, Any]) -> list[str]:
    count = int(data.get("count") or 0)
    if count <= 0:
        return ["- 系统内暂无文档资料记录。", f"- {NO_RECORD_NOTE}"]
    items = data.get("items") or []
    lines = [f"- 系统内共有 {count} 条文档资料记录。"]
    for item in items[:3]:
        lines.append(f"- {item.get('title') or item.get('file_name')}: {item.get('ai_extract_status')}")
    lines.append("- 文件路径和 OCR 全文不会在回答中展示。")
    return lines


def _alert_lines(data: dict[str, Any]) -> list[str]:
    count = int(data.get("count") or 0)
    if count <= 0:
        return ["- 系统内暂无提醒记录。", f"- {NO_RECORD_NOTE}"]
    return [f"- 系统内共有 {count} 条提醒记录。", f"- 当前 active 提醒 {data.get('active_count') or 0} 条。", "- 提醒不是急救服务。"]


def _member_phrase(plan: HealthQueryPlan) -> str:
    return f"{plan.member_label} " if plan.member_label else ""


def _range_phrase(plan: HealthQueryPlan) -> str:
    return f"{plan.time_range.label} "
