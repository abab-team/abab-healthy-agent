from __future__ import annotations

from app.agent.enums import AgentWorkflowName
from app.agent.langgraph.graphs.base import CompiledStateGraphRunner
from app.agent.langgraph.state import BaseAgentGraphState, append_graph_node
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult


class DailyHealthBriefGraph(CompiledStateGraphRunner):
    graph_name = "daily_health_brief_graph"
    workflow_name = AgentWorkflowName.DAILY_HEALTH_BRIEF

    def __init__(self, *, workflow) -> None:
        self.workflow = workflow
        self._context: AgentWorkflowContext | None = None
        self._tool_results = {}
        self._content = ""
        self._message = ""
        super().__init__()

    def _before_run(self, context: AgentWorkflowContext) -> None:
        self._context = context
        self._tool_results = {}
        self._content = ""
        self._message = ""

    def _nodes(self):
        return [
            ("load_member_context", self._load_member_context),
            ("metrics_tool", self._metrics_tool),
            ("blood_pressure_tool", self._blood_pressure_tool),
            ("symptoms_tool", self._symptoms_tool),
            ("alerts_tool", self._alerts_tool),
            ("events_tool", self._events_tool),
            ("brief_builder", self._brief_builder),
            ("critic", self._critic),
            ("optional_store_report", self._optional_store_report),
            ("trace_record", self._trace_record),
        ]

    def _load_member_context(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "load_member_context", metadata={**state.get("metadata", {}), "member_context": "request_context"})

    def _metrics_tool(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        self._call_profile_tool()
        return append_graph_node(state, "metrics_tool", tool_calls_count=1)

    def _blood_pressure_tool(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        self._call_blood_pressure_tool()
        return append_graph_node(state, "blood_pressure_tool", tool_calls_count=2)

    def _symptoms_tool(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        self._call_symptoms_tool()
        return append_graph_node(state, "symptoms_tool", tool_calls_count=3)

    def _alerts_tool(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        self._call_alerts_tool()
        return append_graph_node(state, "alerts_tool", tool_calls_count=4)

    def _events_tool(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        self._call_events_tool()
        return append_graph_node(state, "events_tool", tool_calls_count=5)

    def _brief_builder(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        from app.agent.workflows.daily_health_brief import (
            DEFAULT_DAYS,
            build_daily_health_brief_content,
            maybe_append_daily_brief_rag_context,
            maybe_generate_daily_brief_with_llm,
            _record_llm_safety_summary,
            _record_rag_safety_summary,
        )

        context = self._require_context()
        results = self._build_results()
        rule_content = build_daily_health_brief_content(results, days=DEFAULT_DAYS)
        rule_content, rag_summary = maybe_append_daily_brief_rag_context(context, rule_content, settings=self.workflow.settings)
        llm_attempt = maybe_generate_daily_brief_with_llm(
            results,
            rule_content=rule_content,
            days=DEFAULT_DAYS,
            settings=self.workflow.settings,
            llm_client=self.workflow.llm_client,
        )
        _record_rag_safety_summary(context, rag_summary)
        _record_llm_safety_summary(context, llm_attempt)
        self._content = llm_attempt.content
        self._message = llm_attempt.message
        return append_graph_node(
            state,
            "brief_builder",
            generated_content=self._content[:240],
            metadata={**state.get("metadata", {}), "llm_used": llm_attempt.llm_used, "fallback_used": llm_attempt.fallback_used},
        )

    def _critic(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "critic", critic_flags=["runtime_output_safety"])

    def _optional_store_report(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "optional_store_report", metadata={**state.get("metadata", {}), "stored_report": False})

    def _trace_record(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "trace_record", graph_status="completed")

    def _result_from_state(self, context: AgentWorkflowContext, state: BaseAgentGraphState) -> AgentWorkflowResult:
        from app.agent.workflows.daily_health_brief import READONLY_HEALTH_BRIEF_TOOLS

        return AgentWorkflowResult(
            message=self._message,
            generated_content=self._content,
            tool_calls_count=len(READONLY_HEALTH_BRIEF_TOOLS),
        )

    def _call_profile_tool(self):
        if "profile" not in self._tool_results:
            self._tool_results["profile"] = self.workflow._call_tool(self._require_context(), "health_profile.get", {})
        return self._tool_results["profile"]

    def _call_blood_pressure_tool(self):
        if "blood_pressure" not in self._tool_results:
            from app.agent.workflows.daily_health_brief import DEFAULT_DAYS

            self._tool_results["blood_pressure"] = self.workflow._call_tool(
                self._require_context(), "health_data.blood_pressure.summary", {"days": DEFAULT_DAYS}
            )
        return self._tool_results["blood_pressure"]

    def _call_symptoms_tool(self):
        if "symptoms" not in self._tool_results:
            from app.agent.workflows.daily_health_brief import DEFAULT_DAYS

            self._tool_results["symptoms"] = self.workflow._call_tool(
                self._require_context(), "health_record.symptoms.summary", {"days": DEFAULT_DAYS}
            )
        return self._tool_results["symptoms"]

    def _call_events_tool(self):
        if "followups" not in self._tool_results:
            from app.agent.workflows.daily_health_brief import DEFAULT_LIMIT

            self._tool_results["followups"] = self.workflow._call_tool(
                self._require_context(), "medical_timeline.followups.list", {"limit": DEFAULT_LIMIT}
            )
        return self._tool_results["followups"]

    def _call_alerts_tool(self):
        if "alerts" not in self._tool_results:
            from app.agent.workflows.daily_health_brief import DEFAULT_LIMIT

            self._tool_results["alerts"] = self.workflow._call_tool(self._require_context(), "alerts.active.list", {"limit": DEFAULT_LIMIT})
        return self._tool_results["alerts"]

    def _build_results(self):
        from app.agent.workflows.daily_health_brief import _BriefToolResults

        return _BriefToolResults(
            profile=self._call_profile_tool(),
            blood_pressure=self._call_blood_pressure_tool(),
            symptoms=self._call_symptoms_tool(),
            followups=self._call_events_tool(),
            alerts=self._call_alerts_tool(),
        )

    def _require_context(self) -> AgentWorkflowContext:
        if self._context is None:
            raise RuntimeError("graph context is not initialized")
        return self._context
