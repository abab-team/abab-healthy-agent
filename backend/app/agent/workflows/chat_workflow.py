from __future__ import annotations

from dataclasses import dataclass, replace
import re
from typing import Any

from app.agent import service as agent_service
from app.agent.answer_composer import LLMAnswerComposer
from app.agent.chat import HealthQueryIntent, HealthQueryPlan, SuggestedAction, build_health_insight, parse_health_query, route_conversation
from app.agent.chat.family_context import resolve_family_target
from app.agent.chat.assistant_context import build_assistant_context
from app.agent.chat.responder import ConversationResponder
from app.agent.chat.router import ConversationIntent
from app.agent.conversation import ConversationManager
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

CASUAL_GREETING_TERMS = (
    "joke",
    "\u7b11\u8bdd",
    "你好",
    "您好",
    "嗨",
    "哈喽",
    "谢谢",
    "感谢",
    "再见",
    "拜拜",
    "你能做什么",
    "你可以做什么",
    "怎么用",
    "你是谁",
    "你是做什么的",
    "介绍一下你自己",
)
ENGLISH_CASUAL_GREETING_PATTERN = re.compile(r"\b(?:hello|hi|hey)\b", re.IGNORECASE)


def is_casual_chat_message(message: str) -> bool:
    """Recognize simple conversational turns that need no health-data lookup."""
    text = (message or "").strip().lower()
    return bool(text) and (any(term in text for term in CASUAL_GREETING_TERMS) or bool(ENGLISH_CASUAL_GREETING_PATTERN.search(text)))


def build_casual_chat_response(message: str) -> str:
    text = (message or "").strip().lower()
    if any(term in text for term in ("你是谁", "你是做什么的", "介绍一下你自己")):
        opening = "我是你的 AI 健康管家，主要帮你把系统内已有的健康记录整理得更清楚。"
    elif any(term in text for term in ("谢谢", "感谢")):
        opening = "不客气，我随时可以帮你整理系统内已有的健康记录。"
    elif any(term in text for term in ("再见", "拜拜")):
        opening = "好的，之后需要整理健康记录时再来找我。"
    elif any(term in text for term in ("你能做什么", "你可以做什么", "怎么用")):
        opening = "我可以帮你查询已记录的睡眠、血压、症状、提醒、文档和健康事件，也可以整理健康简报。"
    else:
        opening = "你好，我是你的健康记录整理助手。"
    return "\n".join(
        [
            opening,
            "你可以直接问我：最近一周的睡眠记录怎么样？或爸爸最近有哪些提醒？",
            "涉及健康信息时，我只根据系统内已有记录整理，不替代医生判断。",
        ]
    )


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
        conversation_responder: ConversationResponder | None = None,
        conversation_manager: ConversationManager | None = None,
    ) -> None:
        if executor is None:
            executor = AgentToolExecutor(register_health_query_tools(AgentToolRegistry()))
        self.executor = executor
        self.settings = settings or get_settings()
        self.graph_adapter = graph_adapter or LangGraphExecutionAdapter(self.settings)
        self.planner_service = planner_service or LLMPlannerService(settings=self.settings)
        self.answer_composer = answer_composer or LLMAnswerComposer(settings=self.settings)
        self.critic_service = critic_service or AnswerCriticService(settings=self.settings)
        self.conversation_responder = conversation_responder or ConversationResponder(settings=self.settings)
        self.conversation_manager = conversation_manager or ConversationManager()

    def run(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
        def execute() -> ChatHealthQueryExecution:
            return run_chat_health_query(
                context,
                executor=self.executor,
                settings=self.settings,
                planner_service=self.planner_service,
                answer_composer=self.answer_composer,
                critic_service=self.critic_service,
                conversation_responder=self.conversation_responder,
                conversation_manager=self.conversation_manager,
            )
        def fallback() -> AgentWorkflowResult:
            result = execute()
            return AgentWorkflowResult(
                message=result.answer,
                generated_content=result.answer,
                tool_calls_count=result.tool_calls_count,
                suggested_action=result.suggested_action,
                conversation_task=result.conversation_task,
            )

        # The optional graph only orchestrates this controlled runner. It has
        # no routing, tool, identity, or database authority of its own.
        if self.graph_adapter.chat_query_enabled():
            result = self.graph_adapter.run_chat_health_query(context, execute)
            return AgentWorkflowResult(
                message=result.answer,
                generated_content=result.answer,
                tool_calls_count=result.tool_calls_count,
                suggested_action=result.suggested_action,
                conversation_task=result.conversation_task,
            )
        return fallback()


@dataclass(frozen=True)
class ChatHealthQueryExecution:
    plan: HealthQueryPlan
    answer: str
    tool_calls_count: int
    graph_node_summary: list[str] | None = None
    suggested_action: str | None = None
    conversation_task: dict[str, Any] | None = None


def run_chat_health_query(
    context: AgentWorkflowContext,
    *,
    executor: AgentToolExecutor,
    settings=None,
    planner_service: LLMPlannerService | None = None,
    answer_composer: LLMAnswerComposer | None = None,
    critic_service: AnswerCriticService | None = None,
    conversation_responder: ConversationResponder | None = None,
    conversation_manager: ConversationManager | None = None,
) -> ChatHealthQueryExecution:
    manager = conversation_manager or ConversationManager()
    interruption_plan = parse_health_query(context.request.user_message)
    interruption_route = route_conversation(context.request.user_message, interruption_plan)
    active_task = manager.handle_active_task(context, interruption_route)
    if active_task.handled:
        plan = parse_health_query(context.request.user_message)
        answer = active_task.answer or "当前任务状态暂不可用。"
        _record_session_messages(context, plan, answer)
        return ChatHealthQueryExecution(
            plan=plan,
            answer=answer,
            tool_calls_count=0,
            suggested_action=active_task.suggested_action,
            conversation_task=active_task.task_state,
        )

    memory_context = memory_service.load_session_context(
        context.db,
        user_id=context.request.actor_user_id,
        session_id=context.request.session_id,
    )
    assistant_context = build_assistant_context(context)
    plan = parse_health_query(context.request.user_message)
    plan = memory_service.apply_session_context(context.request.user_message, plan, memory_context)
    route = route_conversation(
        context.request.user_message,
        plan,
        pending_action=memory_context.last_write_action,
    )
    if route.intent == ConversationIntent.RECORD_TASK:
        task_decision = manager.start_record_task(context, route)
        if task_decision.handled:
            answer = task_decision.answer or _write_request_message(route.suggested_action)
            _record_session_messages(context, plan, answer)
            return ChatHealthQueryExecution(
                plan=plan,
                answer=answer,
                tool_calls_count=0,
                suggested_action=task_decision.suggested_action,
                conversation_task=task_decision.task_state,
            )
        answer = _write_request_message(route.suggested_action)
        _record_session_messages(context, plan, answer)
        return ChatHealthQueryExecution(
            plan=plan,
            answer=answer,
            tool_calls_count=0,
            suggested_action=route.suggested_action.value if route.suggested_action else None,
        )
    if route.intent == ConversationIntent.DOCUMENT_TASK:
        answer = (
            "我可以帮你整理已归档的健康资料。请先在资料页选择需要整理的文件或记录，"
            "我会在现有受控流程中生成摘要，不会展示原始长文本或文件路径。"
        )
        _record_session_messages(context, plan, answer)
        return ChatHealthQueryExecution(plan=plan, answer=answer, tool_calls_count=0)
    if route.intent in {ConversationIntent.CASUAL_CHAT, ConversationIntent.OTHER, ConversationIntent.HEALTH_KNOWLEDGE}:
        responder = conversation_responder or ConversationResponder(settings=settings or get_settings())
        answer = responder.respond(
            intent=route.intent,
            user_message=context.request.user_message,
            session_summary=_safe_session_context_summary(memory_context),
            assistant_context=assistant_context,
        )
        _record_session_messages(context, plan, answer)
        return ChatHealthQueryExecution(plan=plan, answer=answer, tool_calls_count=0)
    if plan.is_unknown and (settings or get_settings()).LLM_PLANNER_ENABLED:
        planner = planner_service or LLMPlannerService(settings=settings or get_settings())
        planner_result = planner.plan(
            user_message=context.request.user_message,
            recent_session_context_summary=memory_context.summary_lines,
            safe_memory_summary=(),
        )
        plan = planner_result.plan
        route = route_conversation(context.request.user_message, plan)
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

    resolved_target = resolve_family_target(context, plan)
    if resolved_target.request is None:
        answer = resolved_target.safe_message or "当前无法确认要查询的家庭成员。"
        _record_session_messages(context, plan, answer)
        return ChatHealthQueryExecution(plan=plan, answer=answer, tool_calls_count=0)
    plan = resolved_target.plan
    execution_context = replace(context, request=resolved_target.request)

    if plan.intent == HealthQueryIntent.QUERY_DAILY_STATUS:
        results = _execute_health_overview_tools(execution_context, executor, days=plan.time_range.days)
        answer = _compose_insight_answer(
            plan,
            results,
            conversation_responder=conversation_responder,
            settings=settings,
            user_message=execution_context.request.user_message,
            session_summary=_safe_session_context_summary(memory_context),
            assistant_context=assistant_context,
        )
        answer = _review_answer(
            execution_context,
            critic_service,
            plan=plan,
            answer=answer,
            safe_tool_result_summary=_safe_result_summary(results),
            tool_result_summaries=_tool_result_summaries(results),
        )
        _record_session_messages(execution_context, plan, answer)
        return ChatHealthQueryExecution(plan=plan, answer=answer, tool_calls_count=len(results))

    if plan.intent == HealthQueryIntent.QUERY_MEDICAL_HISTORY:
        results = _execute_medical_history_tools(execution_context, executor, days=plan.time_range.days)
        answer = _compose_insight_answer(
            plan,
            results,
            conversation_responder=conversation_responder,
            settings=settings,
            user_message=execution_context.request.user_message,
            session_summary=_safe_session_context_summary(memory_context),
            assistant_context=assistant_context,
        )
        answer = _review_answer(
            execution_context,
            critic_service,
            plan=plan,
            answer=answer,
            safe_tool_result_summary=_safe_result_summary(results),
            tool_result_summaries=_tool_result_summaries(results),
        )
        _record_session_messages(execution_context, plan, answer)
        return ChatHealthQueryExecution(plan=plan, answer=answer, tool_calls_count=len(results))

    result = _execute_tool(execution_context, executor, plan.tool_name, dict(plan.tool_input or {}))
    answer = _compose_insight_answer(
        plan,
        [result],
        conversation_responder=conversation_responder,
        settings=settings,
        user_message=execution_context.request.user_message,
        session_summary=_safe_session_context_summary(memory_context),
        assistant_context=assistant_context,
    )
    answer = _review_answer(
        execution_context,
        critic_service,
        plan=plan,
        answer=answer,
        safe_tool_result_summary=_safe_result_summary([result]),
        tool_result_summaries=_tool_result_summaries([result]),
    )
    _record_session_messages(execution_context, plan, answer)
    return ChatHealthQueryExecution(plan=plan, answer=answer, tool_calls_count=1)


def _compose_insight_answer(
    plan: HealthQueryPlan,
    results: list[ToolExecutionResult],
    *,
    conversation_responder: ConversationResponder | None,
    settings,
    user_message: str,
    session_summary: tuple[str, ...],
    assistant_context: tuple[str, ...],
) -> str:
    insight = build_health_insight(plan, results)
    responder = conversation_responder or ConversationResponder(settings=settings or get_settings())
    safe_facts = insight.safe_facts()
    if plan.member_label:
        safe_facts = f"本次整理对象：{plan.member_label}\n{safe_facts}"
    return responder.respond(
        intent=ConversationIntent.FAMILY_HEALTH_QUERY if plan.member_scope == "family" else ConversationIntent.HEALTH_RECORD_QUERY,
        user_message=user_message,
        session_summary=session_summary,
        assistant_context=assistant_context,
        safe_facts=safe_facts,
        fallback_answer=insight.render(),
    )


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


def _safe_session_context_summary(memory_context) -> tuple[str, ...]:
    """Pass only routing metadata to a language model, never message content."""
    lines: list[str] = []
    if memory_context.last_member_label:
        lines.append(f"recent member: {memory_context.last_member_label}")
    if memory_context.last_metric_type:
        lines.append(f"recent metric: {memory_context.last_metric_type}")
    if memory_context.last_time_range_label:
        lines.append(f"recent range: {memory_context.last_time_range_label}")
    return tuple(lines)


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


def _execute_health_overview_tools(
    context: AgentWorkflowContext,
    executor: AgentToolExecutor,
    *,
    days: int,
) -> list[ToolExecutionResult]:
    """Collect a member overview only through existing read-only Agent tools.

    The workflow never reads a service or database directly. Each result remains
    permission-gated and traceable by AgentToolExecutor before insight composition.
    """
    calls = (
        ("health_data.metrics.recent", {"days": days, "limit": 10}),
        ("health_data.blood_pressure.summary", {"days": days}),
        ("health_record.symptoms.query", {"days": days}),
        ("documents.query", {"days": days, "limit": 10}),
        ("medical_timeline.events.query", {"days": days, "limit": 10}),
        ("alerts.query", {"days": days, "limit": 10}),
    )
    return [_execute_tool(context, executor, tool_name, input_data) for tool_name, input_data in calls]


def _execute_medical_history_tools(
    context: AgentWorkflowContext,
    executor: AgentToolExecutor,
    *,
    days: int,
) -> list[ToolExecutionResult]:
    """Read only confirmed profile, timeline, and document summaries through ToolExecutor."""
    calls = (
        ("health_profile.get", {}),
        ("medical_timeline.events.query", {"days": days, "limit": 10}),
        ("documents.query", {"limit": 10}),
    )
    return [_execute_tool(context, executor, tool_name, input_data) for tool_name, input_data in calls]


def _write_request_message(action: SuggestedAction | None) -> str:
    if action == SuggestedAction.HEALTH_ALERT:
        return "我可以先帮你整理一条普通健康提醒。下一步会进入预览，预览不会写入；确认后才会创建提醒。"
    if action == SuggestedAction.HEALTH_EVENT_DRAFT:
        return "我可以先帮你整理一份健康事件草稿。预览不会写入，确认后只会创建待确认草稿，不会直接写成正式健康事实。"
    return "我可以先帮你整理一份症状草稿。预览不会写入，确认后只会创建待确认草稿，不会直接写成正式健康事实。"


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
        coverage_note=f"仅基于系统内已有记录；范围：{plan.time_range.label}；天数：{plan.time_range.days}",
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
        part = {
                "tool": result.tool_name,
                "status": result.status,
                "blocked": result.blocked,
                "record_scope": "system_records_only",
                "count": data.get("count") or (data.get("summary") or {}).get("count"),
                "coverage_note": data.get("coverage_note"),
        }
        summary = data.get("summary")
        if isinstance(summary, dict):
            part["facts"] = {
                key: summary.get(key)
                for key in (
                    "metric_type", "days", "count", "latest_value", "latest_measured_at",
                    "avg_value", "min_value", "max_value", "unit", "latest_systolic",
                    "latest_diastolic", "latest_pulse", "avg_systolic", "avg_diastolic",
                    "min_systolic", "max_systolic", "min_diastolic", "max_diastolic",
                )
                if summary.get(key) is not None
            }
        parts.append(part)
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
