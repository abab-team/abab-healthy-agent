from __future__ import annotations

from typing import Protocol

from app.agent.enums import AgentWorkflowName
from app.agent.langgraph.graphs.base import CompiledGraphResult
from app.agent.schemas import AgentWorkflowContext


class AgentGraphRunner(Protocol):
    graph_name: str
    workflow_name: AgentWorkflowName

    def run(self, context: AgentWorkflowContext) -> CompiledGraphResult:
        ...


class AgentGraphRegistry:
    def __init__(self) -> None:
        self._graphs: dict[AgentWorkflowName, AgentGraphRunner] = {}

    def register(self, graph: AgentGraphRunner) -> None:
        self._graphs[graph.workflow_name] = graph

    def get(self, workflow_name: AgentWorkflowName) -> AgentGraphRunner | None:
        return self._graphs.get(workflow_name)

    def list_registered(self) -> dict[str, str]:
        return {workflow.value: graph.graph_name for workflow, graph in self._graphs.items()}
