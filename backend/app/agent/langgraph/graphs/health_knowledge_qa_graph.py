from __future__ import annotations

from app.agent.enums import AgentWorkflowName
from app.agent.langgraph.graphs.base import CompiledStateGraphRunner
from app.agent.langgraph.state import BaseAgentGraphState, append_graph_node
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult


class HealthKnowledgeQAGraph(CompiledStateGraphRunner):
    graph_name = "health_knowledge_qa_graph"
    workflow_name = AgentWorkflowName.HEALTH_KNOWLEDGE_QA_WORKFLOW

    def __init__(self, *, settings) -> None:
        self.settings = settings
        self._context: AgentWorkflowContext | None = None
        self._result: AgentWorkflowResult | None = None
        super().__init__()

    def _before_run(self, context: AgentWorkflowContext) -> None:
        self._context = context
        self._result = None

    def _nodes(self):
        return [
            ("input_safety", self._input_safety),
            ("query_classifier", self._query_classifier),
            ("internal_rag_retrieval", self._internal_rag_retrieval),
            ("answer_builder", self._answer_builder),
            ("critic", self._critic),
            ("trace_record", self._trace_record),
        ]

    def _input_safety(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "input_safety")

    def _query_classifier(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "query_classifier", metadata={**state.get("metadata", {}), "scope": "internal_safe_context_only"})

    def _internal_rag_retrieval(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "internal_rag_retrieval")

    def _answer_builder(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        from app.agent.workflows.health_knowledge_qa_workflow import run_health_knowledge_qa

        self._result = run_health_knowledge_qa(self._require_context(), settings=self.settings)
        return append_graph_node(state, "answer_builder", generated_content=(self._result.generated_content or "")[:240])

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
