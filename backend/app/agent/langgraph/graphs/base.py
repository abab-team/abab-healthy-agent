from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agent import service as agent_service
from app.agent.enums import AgentSafetyLevel, AgentWorkflowName
from app.agent.langgraph.state import BaseAgentGraphState, graph_safe_summary, initial_graph_state
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult


GraphNode = Callable[[BaseAgentGraphState], BaseAgentGraphState]
RouteFunction = Callable[[BaseAgentGraphState], str]


@dataclass(frozen=True)
class CompiledGraphResult:
    result: AgentWorkflowResult
    state: BaseAgentGraphState

    @property
    def node_summary(self) -> list[str]:
        return list(self.state.get("node_summary", []))


class CompiledStateGraphRunner:
    graph_name: str
    workflow_name: AgentWorkflowName

    def __init__(self) -> None:
        self._compiled = self._compile()

    def run(self, context: AgentWorkflowContext) -> CompiledGraphResult:
        trace = agent_service.get_trace(context.db, context.trace_id)
        request_id = trace.request_id if trace is not None else context.request.request_id or str(context.trace_id)
        state = initial_graph_state(
            trace_id=context.trace_id,
            request_id=request_id,
            workflow_name=self.workflow_name.value,
            actor_user_id=context.request.actor_user_id,
            target_user_id=context.request.target_user_id,
            family_id=context.request.family_id,
            user_message=context.request.user_message,
            safety_level=context.safety_level,
            graph_name=self.graph_name,
        )
        self._before_run(context)
        final_state = self._compiled.invoke(state)
        result = self._result_from_state(context, final_state)
        record_graph_node_summary(context, self.workflow_name, self.graph_name, final_state)
        return CompiledGraphResult(result=result, state=final_state)

    def _before_run(self, context: AgentWorkflowContext) -> None:
        return None

    def _compile(self):
        graph = StateGraph(BaseAgentGraphState)
        nodes = self._nodes()
        for name, node in nodes:
            graph.add_node(name, node)
        self._add_edges(graph, [name for name, _ in nodes])
        return graph.compile()

    def _nodes(self) -> list[tuple[str, GraphNode]]:
        raise NotImplementedError

    def _add_edges(self, graph: StateGraph, node_names: list[str]) -> None:
        previous = START
        for name in node_names:
            graph.add_edge(previous, name)
            previous = name
        graph.add_edge(previous, END)

    def _result_from_state(self, context: AgentWorkflowContext, state: BaseAgentGraphState) -> AgentWorkflowResult:
        raise NotImplementedError


def record_graph_node_summary(
    context: AgentWorkflowContext,
    workflow_name: AgentWorkflowName,
    graph_name: str,
    state: BaseAgentGraphState,
) -> None:
    trace = agent_service.get_trace(context.db, context.trace_id)
    if trace is None:
        return
    summary = graph_safe_summary(state)
    agent_service.record_safety_check(
        context.db,
        request_id=trace.request_id,
        workflow_name=workflow_name,
        safety_level=AgentSafetyLevel.SAFE,
        passed=summary.get("graph_status") not in {"failed"},
        intent="graph_node_summary",
        safety_flags=["langgraph", graph_name],
        input_risk_summary="graph_nodes=" + " > ".join(summary.get("node_summary") or []),
        revised_answer_summary=f"safe_graph_state:{summary.get('graph_status')}",
    )
