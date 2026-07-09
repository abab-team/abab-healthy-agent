from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agent.chat import HealthQueryIntent, HealthQueryPlan, parse_health_query
from app.agent.enums import AgentWorkflowName
from app.agent.langgraph.graphs.base import CompiledStateGraphRunner
from app.agent.langgraph.state import BaseAgentGraphState, append_graph_node
from app.agent.memory import service as memory_service
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult


class ChatHealthQueryGraph(CompiledStateGraphRunner):
    graph_name = "chat_health_query_graph"
    workflow_name = AgentWorkflowName.CHAT_WORKFLOW

    def __init__(self, *, executor, settings, planner_service, answer_composer, critic_service) -> None:
        self.executor = executor
        self.settings = settings
        self.planner_service = planner_service
        self.answer_composer = answer_composer
        self.critic_service = critic_service
        self._context: AgentWorkflowContext | None = None
        self._memory_context = None
        self._plan: HealthQueryPlan | None = None
        self._tool_results: list[Any] = []
        self._draft_answer = ""
        self._final_answer = ""
        super().__init__()

    def _before_run(self, context: AgentWorkflowContext) -> None:
        self._context = context
        self._memory_context = None
        self._plan = None
        self._tool_results = []
        self._draft_answer = ""
        self._final_answer = ""

    def _nodes(self):
        return [
            ("load_memory", self._load_memory),
            ("input_safety", self._input_safety),
            ("rule_planner", self._rule_planner),
            ("llm_planner_optional", self._llm_planner_optional),
            ("validate_plan", self._validate_plan),
            ("resolve_member", self._resolve_member),
            ("permission_gate", self._permission_gate),
            ("tool_executor", self._tool_executor),
            ("answer_composer", self._answer_composer),
            ("critic", self._critic),
            ("memory_writer", self._memory_writer),
            ("trace_record", self._trace_record),
        ]

    def _add_edges(self, graph: StateGraph, node_names: list[str]) -> None:
        graph.add_edge(START, "load_memory")
        graph.add_edge("load_memory", "input_safety")
        graph.add_edge("input_safety", "rule_planner")
        graph.add_edge("rule_planner", "llm_planner_optional")
        graph.add_edge("llm_planner_optional", "validate_plan")
        graph.add_conditional_edges(
            "validate_plan",
            self._route_after_plan,
            {
                "clarify": "answer_composer",
                "execute": "resolve_member",
            },
        )
        graph.add_edge("resolve_member", "permission_gate")
        graph.add_edge("permission_gate", "tool_executor")
        graph.add_edge("tool_executor", "answer_composer")
        graph.add_edge("answer_composer", "critic")
        graph.add_edge("critic", "memory_writer")
        graph.add_edge("memory_writer", "trace_record")
        graph.add_edge("trace_record", END)

    def _load_memory(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        context = self._require_context()
        self._memory_context = memory_service.load_session_context(
            context.db,
            user_id=context.request.actor_user_id,
            session_id=context.request.session_id,
        )
        return append_graph_node(state, "load_memory", metadata={**state.get("metadata", {}), "memory_loaded": True})

    def _input_safety(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "input_safety")

    def _rule_planner(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        context = self._require_context()
        plan = parse_health_query(context.request.user_message)
        if self._memory_context is not None:
            plan = memory_service.apply_session_context(context.request.user_message, plan, self._memory_context)
        self._plan = plan
        return append_graph_node(
            state,
            "rule_planner_rule_parse",
            metadata={
                **state.get("metadata", {}),
                "intent": plan.intent.value,
                "member_scope": plan.member_scope,
                "time_range": plan.time_range.label,
                "planner_source": plan.planner_source,
                "has_controlled_mapping": bool(plan.tool_name),
            },
        )

    def _llm_planner_optional(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        context = self._require_context()
        plan = self._require_plan()
        if plan.is_unknown and self.settings.LLM_PLANNER_ENABLED:
            memory_lines = tuple(getattr(self._memory_context, "summary_lines", ()) or ())
            self._plan = self.planner_service.plan(
                user_message=context.request.user_message,
                recent_session_context_summary=memory_lines,
                safe_memory_summary=(),
            ).plan
            return append_graph_node(state, "llm_planner_optional", metadata={**state.get("metadata", {}), "planner_source": "llm_structured_plan"})
        return append_graph_node(state, "llm_planner_optional", metadata={**state.get("metadata", {}), "planner_source": "rule_first"})

    def _validate_plan(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        plan = self._require_plan()
        status = "needs_clarification" if plan.is_unknown or plan.needs_clarification or not plan.tool_name else "valid"
        if plan.intent == HealthQueryIntent.QUERY_DAILY_STATUS:
            status = "valid"
        return append_graph_node(state, "validate_plan", graph_status="planned", metadata={**state.get("metadata", {}), "plan_status": status})

    def _route_after_plan(self, state: BaseAgentGraphState) -> str:
        return "clarify" if state.get("metadata", {}).get("plan_status") == "needs_clarification" else "execute"

    def _resolve_member(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        plan = self._require_plan()
        return append_graph_node(state, "resolve_member", metadata={**state.get("metadata", {}), "member_scope": plan.member_scope})

    def _permission_gate(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "permission_gate", permission_status="delegated_to_tool_executor")

    def _tool_executor(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        from app.agent.workflows import chat_workflow as chat

        context = self._require_context()
        plan = self._require_plan()
        if plan.intent == HealthQueryIntent.QUERY_DAILY_STATUS:
            self._tool_results = [
                chat._execute_tool(context, self.executor, "health_data.metrics.recent", {"days": plan.time_range.days, "limit": 10}),
                chat._execute_tool(context, self.executor, "health_record.symptoms.query", {"days": plan.time_range.days}),
                chat._execute_tool(context, self.executor, "alerts.query", {"days": plan.time_range.days, "limit": 10}),
            ]
        elif plan.tool_name:
            self._tool_results = [chat._execute_tool(context, self.executor, plan.tool_name, dict(plan.tool_input or {}))]
        else:
            self._tool_results = []
        return append_graph_node(
            state,
            "tool_executor",
            tool_calls_count=len(self._tool_results),
            metadata={**state.get("metadata", {}), "tool_executor": "AgentToolExecutor", "tool_call_count": len(self._tool_results)},
        )

    def _answer_composer(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        from app.agent.workflows import chat_workflow as chat

        context = self._require_context()
        plan = self._require_plan()
        if not self._tool_results:
            self._draft_answer = "\n".join([chat._unknown_or_clarification_message(plan), chat.SYSTEM_RECORD_NOTE, chat.SAFETY_FOOTER])
        elif plan.intent == HealthQueryIntent.QUERY_DAILY_STATUS:
            self._draft_answer = chat._compose_daily_status_answer(plan, self._tool_results)
        else:
            self._draft_answer = chat._compose_single_tool_answer(plan, self._tool_results[0])
        if self._tool_results:
            self._draft_answer = chat._maybe_compose_answer(
                self.answer_composer,
                plan=plan,
                fallback_answer=self._draft_answer,
                safe_tool_result_summary=chat._safe_result_summary(self._tool_results),
                user_question_excerpt=context.request.user_message,
            )
        return append_graph_node(state, "answer_composer", generated_content=self._draft_answer[:240])

    def _critic(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        from app.agent.workflows import chat_workflow as chat

        context = self._require_context()
        plan = self._require_plan()
        self._final_answer = chat._review_answer(
            context,
            self.critic_service,
            plan=plan,
            answer=self._draft_answer,
            safe_tool_result_summary=chat._safe_result_summary(self._tool_results),
            tool_result_summaries=chat._tool_result_summaries(self._tool_results),
        )
        flags = ["reviewed"] if self._final_answer == self._draft_answer else ["rewritten"]
        return append_graph_node(state, "critic_review", critic_flags=flags, final_answer=self._final_answer[:240])

    def _memory_writer(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        from app.agent.workflows import chat_workflow as chat

        chat._record_session_messages(self._require_context(), self._require_plan(), self._final_answer)
        return append_graph_node(state, "memory_writer")

    def _trace_record(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "trace_record", graph_status="completed")

    def _result_from_state(self, context: AgentWorkflowContext, state: BaseAgentGraphState) -> AgentWorkflowResult:
        return AgentWorkflowResult(
            message=self._final_answer,
            generated_content=self._final_answer,
            tool_calls_count=int(state.get("tool_calls_count") or 0),
        )

    def _require_context(self) -> AgentWorkflowContext:
        if self._context is None:
            raise RuntimeError("graph context is not initialized")
        return self._context

    def _require_plan(self) -> HealthQueryPlan:
        if self._plan is None:
            raise RuntimeError("graph plan is not initialized")
        return self._plan
