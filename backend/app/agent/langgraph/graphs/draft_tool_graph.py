from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.agent.enums import AgentWorkflowName
from app.agent.langgraph.graphs.base import CompiledStateGraphRunner
from app.agent.langgraph.state import BaseAgentGraphState, append_graph_node
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult, ToolExecutionResult


class DraftToolGraph(CompiledStateGraphRunner):
    graph_name = "draft_tool_graph"

    def __init__(
        self,
        *,
        workflow_name: AgentWorkflowName,
        graph_name: str,
        execute_tool: Callable[[AgentWorkflowContext], ToolExecutionResult],
        build_result: Callable[[ToolExecutionResult], AgentWorkflowResult],
    ) -> None:
        self.workflow_name = workflow_name
        self.graph_name = graph_name
        self._execute_tool_callback = execute_tool
        self._build_result_callback = build_result
        self._context: AgentWorkflowContext | None = None
        self._tool_result: ToolExecutionResult | None = None
        self._workflow_result: AgentWorkflowResult | None = None
        super().__init__()

    def _before_run(self, context: AgentWorkflowContext) -> None:
        self._context = context
        self._tool_result = None
        self._workflow_result = None

    def _nodes(self):
        return [
            ("input_safety", self._input_safety),
            ("resolve_member", self._resolve_member),
            ("permission_gate", self._permission_gate),
            ("draft_tool_executor", self._draft_tool_executor),
            ("draft_response_builder", self._draft_response_builder),
            ("critic", self._critic),
            ("trace_record", self._trace_record),
        ]

    def _input_safety(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "input_safety")

    def _resolve_member(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "resolve_member", metadata={**state.get("metadata", {}), "member_resolution": "request_context"})

    def _permission_gate(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "permission_gate", permission_status="delegated_to_tool_executor")

    def _draft_tool_executor(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        self._tool_result = self._execute_tool_callback(self._require_context())
        status = "blocked" if self._tool_result.blocked or self._tool_result.requires_confirmation else self._tool_result.status
        return append_graph_node(
            state,
            "draft_tool_executor",
            tool_calls_count=1,
            metadata={**state.get("metadata", {}), "tool_status": status, "formal_health_fact_created": False},
        )

    def _draft_response_builder(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        self._workflow_result = self._build_result_callback(self._require_tool_result())
        return append_graph_node(
            state,
            "draft_response_builder",
            generated_content=(self._workflow_result.generated_content or self._workflow_result.message)[:240],
        )

    def _critic(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "critic", critic_flags=["runtime_output_safety"])

    def _trace_record(self, state: BaseAgentGraphState) -> BaseAgentGraphState:
        return append_graph_node(state, "trace_record", graph_status="completed")

    def _result_from_state(self, context: AgentWorkflowContext, state: BaseAgentGraphState) -> AgentWorkflowResult:
        if self._workflow_result is None:
            raise RuntimeError("graph workflow result is not initialized")
        return self._workflow_result

    def _require_context(self) -> AgentWorkflowContext:
        if self._context is None:
            raise RuntimeError("graph context is not initialized")
        return self._context

    def _require_tool_result(self) -> ToolExecutionResult:
        if self._tool_result is None:
            raise RuntimeError("graph tool result is not initialized")
        return self._tool_result
