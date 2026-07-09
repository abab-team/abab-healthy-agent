from __future__ import annotations

from app.agent.enums import AgentWorkflowName
from app.agent.langgraph.graphs.base import CompiledStateGraphRunner
from app.agent.langgraph.state import BaseAgentGraphState, append_graph_node
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult


class DailyReportGraph(CompiledStateGraphRunner):
    graph_name = "daily_report_graph"
    workflow_name = AgentWorkflowName.DAILY_REPORT_WORKFLOW

    def __init__(self, *, workflow) -> None:
        self.workflow = workflow
        self._context: AgentWorkflowContext | None = None
        self._result: AgentWorkflowResult | None = None
        super().__init__()

    def _before_run(self, context: AgentWorkflowContext) -> None:
        self._context = context
        self._result = None

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
        return append_graph_node(state, "load_member_context")

    def _metrics_tool(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "metrics_tool")

    def _blood_pressure_tool(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "blood_pressure_tool")

    def _symptoms_tool(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "symptoms_tool")

    def _alerts_tool(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "alerts_tool")

    def _events_tool(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "events_tool")

    def _brief_builder(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        from app.agent.workflows.daily_report_workflow import run_daily_report_workflow

        self._result = run_daily_report_workflow(self._require_context(), daily_brief_workflow=self.workflow.daily_brief_workflow)
        return append_graph_node(state, "brief_builder", generated_content=(self._result.generated_content or "")[:240], tool_calls_count=self._result.tool_calls_count)

    def _critic(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "critic", critic_flags=["runtime_output_safety"])

    def _optional_store_report(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "optional_store_report", metadata={**state.get("metadata", {}), "stored_report": False})

    def _trace_record(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "trace_record", graph_status="completed")

    def _result_from_state(self, context: AgentWorkflowContext, state: BaseAgentGraphState) -> AgentWorkflowResult:
        if self._result is None:
            raise RuntimeError("graph result is not initialized")
        return self._result

    def _require_context(self) -> AgentWorkflowContext:
        if self._context is None:
            raise RuntimeError("graph context is not initialized")
        return self._context
