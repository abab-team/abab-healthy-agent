from __future__ import annotations

from app.agent.enums import AgentWorkflowName
from app.agent.langgraph.graphs.base import CompiledStateGraphRunner
from app.agent.langgraph.state import BaseAgentGraphState, append_graph_node
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult


class DoctorVisitSummaryGraph(CompiledStateGraphRunner):
    graph_name = "doctor_visit_summary_graph"
    workflow_name = AgentWorkflowName.DOCTOR_VISIT_SUMMARY_WORKFLOW

    def __init__(self, *, workflow) -> None:
        self.workflow = workflow
        self._context: AgentWorkflowContext | None = None
        self._tool_results = {}
        self._content = ""
        super().__init__()

    def _before_run(self, context: AgentWorkflowContext) -> None:
        self._context = context
        self._tool_results = {}
        self._content = ""

    def _nodes(self):
        return [
            ("input_safety", self._input_safety),
            ("options_parser", self._options_parser),
            ("resolve_member", self._resolve_member),
            ("permission_gate", self._permission_gate),
            ("blood_pressure_tool", self._blood_pressure_tool),
            ("symptoms_tool", self._symptoms_tool),
            ("events_tool", self._events_tool),
            ("documents_tool", self._documents_tool),
            ("alerts_tool", self._alerts_tool),
            ("summary_builder", self._summary_builder),
            ("critic", self._critic),
            ("trace_record", self._trace_record),
        ]

    def _input_safety(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "input_safety")

    def _options_parser(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        from app.agent.workflows.doctor_visit_summary_workflow import _workflow_options

        options = _workflow_options(self._require_context())
        return append_graph_node(state, "options_parser", metadata={**state.get("metadata", {}), "days": options.days, "limit": options.limit})

    def _resolve_member(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "resolve_member", metadata={**state.get("metadata", {}), "member_resolution": "request_context"})

    def _permission_gate(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "permission_gate", permission_status="delegated_to_tool_executor")

    def _blood_pressure_tool(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        self._call_blood_pressure_tool()
        return append_graph_node(state, "blood_pressure_tool", tool_calls_count=1)

    def _symptoms_tool(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        self._call_symptoms_tool()
        return append_graph_node(state, "symptoms_tool", tool_calls_count=2)

    def _events_tool(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        self._call_events_tool()
        return append_graph_node(state, "events_tool", tool_calls_count=3)

    def _documents_tool(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        self._call_documents_tool()
        return append_graph_node(state, "documents_tool", tool_calls_count=4)

    def _alerts_tool(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        self._call_alerts_tool()
        return append_graph_node(state, "alerts_tool", tool_calls_count=5)

    def _summary_builder(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        from app.agent.workflows.doctor_visit_summary_workflow import build_doctor_visit_summary_content, _workflow_options

        options = _workflow_options(self._require_context())
        self._content = build_doctor_visit_summary_content(self._build_results(), days=options.days)
        return append_graph_node(state, "summary_builder", generated_content=self._content[:240])

    def _critic(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "critic", critic_flags=["runtime_output_safety"])

    def _trace_record(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "trace_record", graph_status="completed")

    def _result_from_state(self, context: AgentWorkflowContext, state: BaseAgentGraphState) -> AgentWorkflowResult:
        from app.agent.workflows.doctor_visit_summary_workflow import DOCTOR_SUMMARY_TOOLS

        return AgentWorkflowResult(
            message="Doctor visit preparation package generated from system records.",
            generated_content=self._content,
            tool_calls_count=len(DOCTOR_SUMMARY_TOOLS),
        )

    def _call_blood_pressure_tool(self):
        if "blood_pressure" not in self._tool_results:
            from app.agent.workflows.doctor_visit_summary_workflow import _workflow_options

            options = _workflow_options(self._require_context())
            self._tool_results["blood_pressure"] = self.workflow._call_tool(
                self._require_context(), "health_data.blood_pressure.summary", {"days": options.days}
            )
        return self._tool_results["blood_pressure"]

    def _call_symptoms_tool(self):
        if "symptoms" not in self._tool_results:
            from app.agent.workflows.doctor_visit_summary_workflow import _workflow_options

            options = _workflow_options(self._require_context())
            self._tool_results["symptoms"] = self.workflow._call_tool(
                self._require_context(), "health_record.symptoms.query", {"days": options.days}
            )
        return self._tool_results["symptoms"]

    def _call_events_tool(self):
        if "events" not in self._tool_results:
            from app.agent.workflows.doctor_visit_summary_workflow import _workflow_options

            options = _workflow_options(self._require_context())
            self._tool_results["events"] = self.workflow._call_tool(
                self._require_context(), "medical_timeline.events.query", {"days": options.days}
            )
        return self._tool_results["events"]

    def _call_documents_tool(self):
        if "documents" not in self._tool_results:
            from app.agent.workflows.doctor_visit_summary_workflow import _workflow_options

            options = _workflow_options(self._require_context())
            self._tool_results["documents"] = self.workflow._call_tool(self._require_context(), "documents.query", {"limit": options.limit})
        return self._tool_results["documents"]

    def _call_alerts_tool(self):
        if "alerts" not in self._tool_results:
            from app.agent.workflows.doctor_visit_summary_workflow import _workflow_options

            options = _workflow_options(self._require_context())
            self._tool_results["alerts"] = self.workflow._call_tool(self._require_context(), "alerts.query", {"limit": options.limit})
        return self._tool_results["alerts"]

    def _build_results(self):
        from app.agent.workflows.doctor_visit_summary_workflow import _DoctorVisitToolResults

        return _DoctorVisitToolResults(
            blood_pressure=self._call_blood_pressure_tool(),
            symptoms=self._call_symptoms_tool(),
            events=self._call_events_tool(),
            documents=self._call_documents_tool(),
            alerts=self._call_alerts_tool(),
        )

    def _require_context(self) -> AgentWorkflowContext:
        if self._context is None:
            raise RuntimeError("graph context is not initialized")
        return self._context
