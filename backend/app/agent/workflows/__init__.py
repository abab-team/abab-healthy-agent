from __future__ import annotations

from typing import Protocol

from app.agent.enums import AgentWorkflowName
from app.agent.exceptions import AgentWorkflowNotRegisteredError
from app.agent.schemas import AgentRunRequest, AgentWorkflowResult


NO_OP_AGENT_MESSAGE = "Agent runtime is ready. No AI workflow has been executed in this phase."


class AgentWorkflowHandler(Protocol):
    workflow_name: AgentWorkflowName

    def run(self, request: AgentRunRequest) -> AgentWorkflowResult:
        ...


class NoOpHealthAssistantWorkflow:
    workflow_name = AgentWorkflowName.CHAT_WORKFLOW

    def run(self, request: AgentRunRequest) -> AgentWorkflowResult:
        return AgentWorkflowResult(
            message=NO_OP_AGENT_MESSAGE,
            generated_content=NO_OP_AGENT_MESSAGE,
            tool_calls_count=0,
        )


class AgentWorkflowRegistry:
    def __init__(self) -> None:
        self._handlers: dict[AgentWorkflowName, AgentWorkflowHandler] = {}

    def register(self, handler: AgentWorkflowHandler) -> None:
        self._handlers[handler.workflow_name] = handler

    def get(self, workflow_name: AgentWorkflowName) -> AgentWorkflowHandler:
        handler = self._handlers.get(workflow_name)
        if handler is None:
            raise AgentWorkflowNotRegisteredError("workflow handler is not registered")
        return handler


def default_workflow_registry() -> AgentWorkflowRegistry:
    registry = AgentWorkflowRegistry()
    registry.register(NoOpHealthAssistantWorkflow())
    return registry
