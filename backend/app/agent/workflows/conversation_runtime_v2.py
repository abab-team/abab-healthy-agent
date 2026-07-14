"""Feature-flagged bridge from the Agent runtime to Conversation Runtime V2."""

from __future__ import annotations

from uuid import UUID

from app.agent.conversation_v2 import ConversationAccessDeniedError, ConversationRuntimeV2
from app.agent.conversation_v2.adapters.legacy_session_adapter import mirror_turn_for_display
from app.agent.memory import service as memory_service
from app.agent.enums import AgentWorkflowName
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult
from app.agent.workflows.chat_workflow import ChatHealthQueryWorkflow
from app.core.config import Settings, get_settings


class ConversationRuntimeWorkflow:
    """Dispatch to V2 only when explicitly enabled; otherwise use legacy chat."""

    workflow_name = AgentWorkflowName.CHAT_WORKFLOW

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        legacy_workflow: ChatHealthQueryWorkflow | None = None,
        runtime_v2_factory=None,
        display_mirror=mirror_turn_for_display,
    ) -> None:
        self.settings = settings or get_settings()
        self.legacy_workflow = legacy_workflow or ChatHealthQueryWorkflow(settings=self.settings)
        self.runtime_v2_factory = runtime_v2_factory or self._new_runtime_v2
        self.display_mirror = display_mirror

    def run(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
        if not self.settings.CONVERSATION_RUNTIME_V2_ENABLED:
            return self.legacy_workflow.run(context)
        if not context.request.session_id:
            return AgentWorkflowResult(
                message="A conversation session is required before continuing this chat.",
                generated_content="A conversation session is required before continuing this chat.",
            )
        runtime = self.runtime_v2_factory(context)
        try:
            result = runtime.run_turn(
                session_id=context.request.session_id,
                user_id=context.request.actor_user_id,
                user_message=context.request.user_message,
                request_id=context.request.request_id,
            )
        except ConversationAccessDeniedError:
            return AgentWorkflowResult(
                message="This conversation is not available for the current user.",
                generated_content="This conversation is not available for the current user.",
            )
        self.display_mirror(
            context.db,
            session_id=context.request.session_id,
            user_message=context.request.user_message,
            assistant_message=result.answer,
        )
        return AgentWorkflowResult(message=result.answer, generated_content=result.answer)

    def _new_runtime_v2(self, context: AgentWorkflowContext) -> ConversationRuntimeV2:
        def owner_resolver(session_id: str) -> UUID | None:
            session = memory_service.get_session_for_user(
                context.db,
                session_id=session_id,
                user_id=context.request.actor_user_id,
            )
            return session.user_id if session is not None else None

        return ConversationRuntimeV2(settings=self.settings, owner_resolver=owner_resolver)
