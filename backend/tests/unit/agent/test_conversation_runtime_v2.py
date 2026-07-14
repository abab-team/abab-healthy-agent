from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage

from app.agent.conversation_v2.checkpointer import PersistentConversationCheckpointer
from app.agent.conversation_v2.message_safety import sanitize_checkpoint_message
from app.agent.conversation_v2.service import ConversationAccessDeniedError, ConversationRuntimeV2
from app.agent.enums import AgentWorkflowName
from app.agent.schemas import AgentRunRequest, AgentWorkflowContext, AgentWorkflowResult
from app.agent.workflows.conversation_runtime_v2 import ConversationRuntimeWorkflow
from app.core.config import Settings
from app.llm.schemas import LLMResponse


class ConversationRuntimeV2TestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.checkpoint_path = Path(self.temp_dir.name) / "conversation.sqlite3"
        self.owner = uuid4()
        self.other_user = uuid4()
        self.session_one = uuid4()
        self.session_two = uuid4()
        self.owners = {str(self.session_one): self.owner, str(self.session_two): self.other_user}
        self.settings = Settings(
            CONVERSATION_RUNTIME_V2_ENABLED=True,
            CONVERSATION_RUNTIME_V2_MAX_MESSAGES=6,
            LLM_ENABLED=False,
        )
        self.runtime = self._runtime()

    def tearDown(self) -> None:
        self.runtime.close()
        self.temp_dir.cleanup()

    def _runtime(self) -> ConversationRuntimeV2:
        return ConversationRuntimeV2(
            settings=self.settings,
            checkpointer=PersistentConversationCheckpointer(self.checkpoint_path),
            owner_resolver=lambda session_id: self.owners.get(session_id),
        )

    def test_persists_standard_human_and_ai_messages_in_order(self) -> None:
        result = self.runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message="hello")

        self.assertEqual(result.thread_id, str(self.session_one))
        self.assertEqual(type(self.runtime.graph.checkpointer).__name__, "SqliteSaver")
        self.assertEqual([message.type for message in result.messages], ["system", "human", "ai"])
        self.assertIsInstance(result.messages[1], HumanMessage)
        self.assertIsInstance(result.messages[2], AIMessage)

    def test_checkpoint_restores_after_runtime_restart(self) -> None:
        self.runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message="first turn")
        self.runtime.close()
        self.runtime = self._runtime()

        restored = self.runtime.get_messages(session_id=self.session_one, user_id=self.owner)

        self.assertEqual([message.type for message in restored], ["system", "human", "ai"])
        self.assertEqual(str(restored[1].content), "first turn")

    def test_sessions_and_users_are_isolated(self) -> None:
        self.runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message="owner message")
        self.runtime.run_turn(session_id=self.session_two, user_id=self.other_user, user_message="other message")

        one = self.runtime.get_messages(session_id=self.session_one, user_id=self.owner)
        two = self.runtime.get_messages(session_id=self.session_two, user_id=self.other_user)

        self.assertIn("owner message", str(one[1].content))
        self.assertIn("other message", str(two[1].content))
        with self.assertRaises(ConversationAccessDeniedError):
            self.runtime.get_messages(session_id=self.session_one, user_id=self.other_user)

    def test_ten_turns_keep_recent_bounded_history(self) -> None:
        for index in range(10):
            self.runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message=f"turn {index}")

        messages = self.runtime.get_messages(session_id=self.session_one, user_id=self.owner)

        self.assertLessEqual(len(messages), self.settings.CONVERSATION_RUNTIME_V2_MAX_MESSAGES)
        self.assertIn("turn 9", str(messages[-2].content))

    def test_llm_receives_standard_message_roles_without_prompt_aggregation(self) -> None:
        client = _RecordingLLMClient()
        settings = Settings(
            CONVERSATION_RUNTIME_V2_ENABLED=True,
            CONVERSATION_RUNTIME_V2_MAX_MESSAGES=8,
            LLM_ENABLED=True,
            LLM_CHAT_ENABLED=True,
        )
        runtime = ConversationRuntimeV2(
            settings=settings,
            checkpointer=PersistentConversationCheckpointer(self.checkpoint_path),
            owner_resolver=lambda session_id: self.owners.get(session_id),
            llm_client=client,
        )
        try:
            runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message="first")
            runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message="second")
        finally:
            runtime.close()

        self.assertEqual(
            [(message.role, message.content) for message in client.calls[-1]],
            [
                ("system", "You are a friendly family health assistant. Hold a natural conversation, but do not claim to access health records or invoke tools. Keep replies concise."),
                ("user", "first"),
                ("assistant", "recorded reply"),
                ("user", "second"),
            ],
        )

    def test_checkpoint_sanitizes_secrets_paths_and_long_pastes(self) -> None:
        raw = "api_key=secret-value C:\\users\\private.txt SELECT * FROM records\n" + ("x" * 1800)
        safe = sanitize_checkpoint_message(raw)
        self.runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message=raw)
        messages = self.runtime.get_messages(session_id=self.session_one, user_id=self.owner)

        self.assertIn("[redacted]", safe)
        self.assertNotIn("secret-value", str(messages[1].content))
        self.assertNotIn("C:\\users", str(messages[1].content).lower())
        self.assertNotIn("SELECT", str(messages[1].content))
        self.assertIn("[long content omitted]", str(messages[1].content))

    def test_feature_flag_keeps_legacy_workflow_as_rollback_path(self) -> None:
        legacy = _WorkflowResult("legacy")
        v2 = _ConversationResult("v2")
        context = _context(self.owner, self.session_one)

        disabled = ConversationRuntimeWorkflow(
            settings=Settings(CONVERSATION_RUNTIME_V2_ENABLED=False),
            legacy_workflow=legacy,
            runtime_v2_factory=lambda _: v2,
        )
        enabled = ConversationRuntimeWorkflow(
            settings=Settings(CONVERSATION_RUNTIME_V2_ENABLED=True),
            legacy_workflow=legacy,
            runtime_v2_factory=lambda _: v2,
            display_mirror=lambda *_, **__: None,
        )

        self.assertEqual(disabled.run(context).generated_content, "legacy")
        self.assertEqual(enabled.run(context).generated_content, "v2")
        self.assertEqual(legacy.calls, 1)
        self.assertEqual(v2.calls, 1)


class _WorkflowResult:
    workflow_name = AgentWorkflowName.CHAT_WORKFLOW

    def __init__(self, content: str) -> None:
        self.content = content
        self.calls = 0

    def run(self, context):  # noqa: ANN001
        self.calls += 1
        return AgentWorkflowResult(message=self.content, generated_content=self.content)


class _ConversationResult:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.calls = 0

    def run_turn(self, **kwargs):  # noqa: ANN003
        self.calls += 1
        return type("Result", (), {"answer": self.answer})()


class _RecordingLLMClient:
    def __init__(self) -> None:
        self.calls = []

    def chat(self, messages, **kwargs):  # noqa: ANN001, ANN003
        self.calls.append(messages)
        return LLMResponse(
            content="recorded reply",
            provider="test",
            model="test",
            is_mock=True,
        )


def _context(user_id, session_id):  # noqa: ANN001
    request = AgentRunRequest(
        actor_user_id=user_id,
        target_user_id=user_id,
        workflow_type=AgentWorkflowName.CHAT_WORKFLOW,
        user_message="hello",
        session_id=str(session_id),
    )
    return AgentWorkflowContext(db=None, trace_id=uuid4(), request=request, safety_level="safe")


if __name__ == "__main__":
    unittest.main()
