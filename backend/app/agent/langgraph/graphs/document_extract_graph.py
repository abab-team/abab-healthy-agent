from __future__ import annotations

from app.agent.enums import AgentWorkflowName
from app.agent.langgraph.graphs.base import CompiledStateGraphRunner
from app.agent.langgraph.state import BaseAgentGraphState, append_graph_node
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult


class DocumentExtractGraph(CompiledStateGraphRunner):
    graph_name = "document_extract_graph"
    workflow_name = AgentWorkflowName.DOCUMENT_EXTRACT_WORKFLOW

    def __init__(self, *, workflow) -> None:
        self.workflow = workflow
        self._context: AgentWorkflowContext | None = None
        self._tool_result = None
        self._result: AgentWorkflowResult | None = None
        super().__init__()

    def _before_run(self, context: AgentWorkflowContext) -> None:
        self._context = context
        self._tool_result = None
        self._result = None

    def _nodes(self):
        return [
            ("input_safety", self._input_safety),
            ("document_context_loader", self._document_context_loader),
            ("document_permission_gate", self._document_permission_gate),
            ("ocr_or_text_extract", self._ocr_or_text_extract),
            ("document_summary_builder", self._document_summary_builder),
            ("medical_event_draft_builder", self._medical_event_draft_builder),
            ("critic", self._critic),
            ("trace_record", self._trace_record),
        ]

    def _input_safety(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "input_safety")

    def _document_context_loader(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        self._tool_result = self.workflow.call_documents_query(self._require_context())
        return append_graph_node(state, "document_context_loader", tool_calls_count=1)

    def _document_permission_gate(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        status = "blocked" if self._tool_result is not None and self._tool_result.blocked else "delegated_to_tool_executor"
        return append_graph_node(state, "document_permission_gate", permission_status=status)

    def _ocr_or_text_extract(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "ocr_or_text_extract", metadata={**state.get("metadata", {}), "ocr_mode": "metadata_or_mock_preview"})

    def _document_summary_builder(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "document_summary_builder")

    def _medical_event_draft_builder(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        from app.agent.workflows.document_extract_workflow import build_document_extract_result

        self._result = build_document_extract_result(self._require_context(), self._tool_result)
        return append_graph_node(state, "medical_event_draft_builder", generated_content=(self._result.generated_content or "")[:240])

    def _critic(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "critic", critic_flags=["runtime_output_safety"])

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
