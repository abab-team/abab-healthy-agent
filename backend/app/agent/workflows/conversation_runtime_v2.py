"""Feature-flagged bridge from the Agent runtime to Conversation Runtime V2."""

from __future__ import annotations

from uuid import UUID

from app.agent.conversation_v2 import ConversationAccessDeniedError, ConversationRuntimeV2
from app.agent.conversation_v2.adapters.legacy_session_adapter import mirror_turn_for_display
from app.agent.conversation_v2.business_tool_runtime import ConversationBusinessToolRuntime
from app.agent.memory import service as memory_service
from app.agent.enums import AgentWorkflowName
from app.agent.schemas import AgentWorkflowContext, AgentWorkflowResult, ToolExecutionRequest
from app.agent.tool_executor import AgentToolExecutor
from app.agent.tool_registry import AgentToolRegistry
from app.agent.tools import register_health_query_tools
from app.core.config import Settings, get_settings
from app.modules.identity import service as identity_service


class ConversationRuntimeWorkflow:
    """The single conversation entry point backed by the V3 Agent loop.

    Legacy chat workflows and ConversationManager never decide a chat turn.
    The optional display mirror is write-only and cannot influence reasoning.
    """

    workflow_name = AgentWorkflowName.CHAT_WORKFLOW

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        executor: AgentToolExecutor | None = None,
        runtime_v2_factory=None,
        display_mirror=mirror_turn_for_display,
    ) -> None:
        self.settings = settings or get_settings()
        self.executor = executor or AgentToolExecutor(register_health_query_tools(AgentToolRegistry()))
        self.runtime_v2_factory = runtime_v2_factory or self._new_runtime_v2
        self.display_mirror = display_mirror

    def run(self, context: AgentWorkflowContext) -> AgentWorkflowResult:
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
                quick_note_mode=bool((context.request.workflow_payload or {}).get("quick_note_mode")),
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
        return AgentWorkflowResult(
            message=result.answer,
            generated_content=result.answer,
            tool_calls_count=int(getattr(result, "tool_calls_count", 0) or 0),
            conversation_task=getattr(result, "conversation_task", None),
        )

    def _new_runtime_v2(self, context: AgentWorkflowContext) -> ConversationRuntimeV2:
        def owner_resolver(session_id: str) -> UUID | None:
            session = memory_service.get_session_for_user(
                context.db,
                session_id=session_id,
                user_id=context.request.actor_user_id,
            )
            return session.user_id if session is not None else None

        user = identity_service.get_user(context.db, context.request.actor_user_id)
        tool_runtime = ConversationBusinessToolRuntime(context=context, executor=self.executor)

        def create_draft_candidate(candidate: dict):
            execution = self.executor.execute(
                context.db,
                ToolExecutionRequest(
                    trace_id=context.trace_id,
                    tool_name="conversation.quick_note_draft.create",
                    actor_user_id=context.request.actor_user_id,
                    target_user_id=context.request.actor_user_id,
                    family_id=None,
                    input_data={"candidate": candidate, "session_id": context.request.session_id},
                    confirmed=False,
                    safety_level=context.safety_level,
                    reason="conversation_quick_note_candidate",
                ),
            )
            return execution.output_data if not execution.blocked and isinstance(execution.output_data, dict) else None

        return ConversationRuntimeV2(
            settings=self.settings,
            owner_resolver=owner_resolver,
            tool_runtime=tool_runtime,
            draft_candidate_creator=create_draft_candidate,
            user_context={"name": (getattr(user, "nickname", None) or "")},
        )
