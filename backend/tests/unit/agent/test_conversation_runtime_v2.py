from __future__ import annotations

import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.agent.conversation_v2.checkpointer import PersistentConversationCheckpointer
from app.agent.conversation_v2.message_safety import sanitize_checkpoint_message
from app.agent.conversation_v2.service import SYSTEM_PROMPT, TOOL_CALL_POLICY, ConversationAccessDeniedError, ConversationRuntimeV2
from app.agent.conversation_v2.business_tool_runtime import BusinessToolCall, BusinessToolExecution
from app.agent.conversation_v2.tool_runtime import ConversationToolPlan, PlannedToolCall, safe_tool_result
from app.agent.chat.schemas import HealthQueryIntent, HealthQueryPlan, HealthQueryTimeRange
from app.agent.schemas import ToolExecutionResult
from app.agent.enums import AgentWorkflowName
from app.agent.schemas import AgentRunRequest, AgentWorkflowContext, AgentWorkflowResult
from app.agent.runtime import _normalize_chat_output_for_harness
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
        for message in ("learning LangGraph", "I care about persistence", "I am building a health agent"):
            self.runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message=message)
        self.runtime.close()
        self.runtime = self._runtime()

        restored = self.runtime.get_messages(session_id=self.session_one, user_id=self.owner)

        self.assertEqual([message.type for message in restored], ["system", "human", "ai", "human", "ai"])
        self.assertIn("health agent", str(restored[-2].content))
        self.assertEqual(sum(isinstance(message, SystemMessage) for message in restored), 1)

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

    def test_fifty_turns_remain_bounded_and_keep_message_order(self) -> None:
        for index in range(50):
            self.runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message=f"load {index}")

        messages = self.runtime.get_messages(session_id=self.session_one, user_id=self.owner)

        self.assertLessEqual(len(messages), self.settings.CONVERSATION_RUNTIME_V2_MAX_MESSAGES)
        self.assertEqual(messages[0].type, "system")
        self.assertEqual([message.type for message in messages[1:]], ["human", "ai", "human", "ai"])
        self.assertIn("load 49", str(messages[-2].content))

    def test_same_thread_requests_are_serialized_without_message_loss(self) -> None:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(
                    self.runtime.run_turn,
                    session_id=self.session_one,
                    user_id=self.owner,
                    user_message=message,
                )
                for message in ("parallel one", "parallel two")
            ]
            for future in futures:
                future.result()

        messages = self.runtime.get_messages(session_id=self.session_one, user_id=self.owner)
        human_messages = [str(message.content) for message in messages if isinstance(message, HumanMessage)]
        self.assertCountEqual(human_messages, ["parallel one", "parallel two"])
        self.assertEqual([message.type for message in messages], ["system", "human", "ai", "human", "ai"])

    def test_same_request_id_is_not_appended_twice(self) -> None:
        first = self.runtime.run_turn(
            session_id=self.session_one,
            user_id=self.owner,
            user_message="retry-safe message",
            request_id="request-retry-001",
        )
        repeated = self.runtime.run_turn(
            session_id=self.session_one,
            user_id=self.owner,
            user_message="retry-safe message",
            request_id="request-retry-001",
        )

        self.assertEqual(first.answer, repeated.answer)
        self.assertEqual([message.type for message in repeated.messages], ["system", "human", "ai"])

    def test_tool_message_pair_is_persisted_and_trimmed_as_one_turn(self) -> None:
        tool_settings = Settings(
            CONVERSATION_RUNTIME_V2_ENABLED=True,
            CONVERSATION_RUNTIME_V2_MAX_MESSAGES=7,
            LLM_ENABLED=False,
        )
        tool_runtime = ConversationRuntimeV2(
            settings=tool_settings,
            checkpointer=PersistentConversationCheckpointer(Path(self.temp_dir.name) / "tool.sqlite3"),
            owner_resolver=lambda session_id: self.owners.get(session_id),
        )
        config = {"configurable": {"thread_id": str(self.session_one)}}
        tool_call_id = "safe-tool-call-1"
        try:
            tool_runtime.graph.update_state(
                config,
                {
                    "messages": [
                        SystemMessage(content="system"),
                        HumanMessage(content="tool context"),
                        AIMessage(
                            content="",
                            tool_calls=[{"name": "safe_lookup", "args": {}, "id": tool_call_id, "type": "tool_call"}],
                        ),
                        ToolMessage(content="safe result", tool_call_id=tool_call_id),
                        AIMessage(content="tool result summarized"),
                    ]
                },
            )
            tool_runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message="continue")
            messages = tool_runtime.get_messages(session_id=self.session_one, user_id=self.owner)
        finally:
            tool_runtime.close()

        tool_messages = [message for message in messages if isinstance(message, ToolMessage)]
        tool_call_messages = [message for message in messages if isinstance(message, AIMessage) and message.tool_calls]
        self.assertEqual(len(tool_messages), 1)
        self.assertEqual(len(tool_call_messages), 1)
        self.assertEqual(tool_messages[0].tool_call_id, tool_call_messages[0].tool_calls[0]["id"])

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

        messages = client.calls[-1]
        self.assertEqual([message.role for message in messages], ["system", "user", "assistant", "user"])
        self.assertIn("健康小伙伴", messages[0].content)
        self.assertIn(SYSTEM_PROMPT, messages[0].content)
        self.assertIn(TOOL_CALL_POLICY, messages[0].content)
        self.assertEqual([message.content for message in messages[1:]], ["first", "recorded reply", "second"])

    def test_checkpoint_sanitizes_secrets_paths_and_long_pastes(self) -> None:
        raw = "api_key=secret-value \u5bc6\u7801\u662f abc123456 \u8eab\u4efd\u8bc1\u53f7 123456789012345678 C:\\users\\private.txt SELECT * FROM records\n" + ("x" * 1800)
        safe = sanitize_checkpoint_message(raw)
        self.runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message=raw)
        messages = self.runtime.get_messages(session_id=self.session_one, user_id=self.owner)

        self.assertIn("[redacted]", safe)
        self.assertNotIn("secret-value", str(messages[1].content))
        self.assertNotIn("abc123456", str(messages[1].content))
        self.assertNotIn("123456789012345678", str(messages[1].content))
        self.assertNotIn("C:\\users", str(messages[1].content).lower())
        self.assertNotIn("SELECT", str(messages[1].content))
        self.assertIn("[long content omitted]", str(messages[1].content))

    def test_llm_failure_uses_nonempty_controlled_fallback(self) -> None:
        settings = Settings(CONVERSATION_RUNTIME_V2_ENABLED=True, LLM_ENABLED=True, LLM_CHAT_ENABLED=True)
        runtime = ConversationRuntimeV2(
            settings=settings,
            checkpointer=PersistentConversationCheckpointer(Path(self.temp_dir.name) / "failure.sqlite3"),
            owner_resolver=lambda session_id: self.owners.get(session_id),
            llm_client=_FailingLLMClient(),
        )
        try:
            result = runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message="hello")
        finally:
            runtime.close()

        self.assertTrue(result.answer)
        self.assertNotIn("traceback", result.answer.lower())

    def test_output_safety_replaces_assurance_claim_from_direct_agent_reply(self) -> None:
        settings = Settings(CONVERSATION_RUNTIME_V2_ENABLED=True, LLM_ENABLED=True, LLM_CHAT_ENABLED=True)
        runtime = ConversationRuntimeV2(
            settings=settings,
            checkpointer=PersistentConversationCheckpointer(Path(self.temp_dir.name) / "assurance.sqlite3"),
            owner_resolver=lambda session_id: self.owners.get(session_id),
            llm_client=_AssuranceLLMClient(),
        )
        try:
            result = runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message="hello")
        finally:
            runtime.close()

        self.assertNotIn("可以放心", result.answer)
        self.assertIn("确定性的健康结论", result.answer)

    def test_harness_keeps_general_reference_after_removing_diagnostic_sentence(self) -> None:
        output = _normalize_chat_output_for_harness(
            "这次是118/76 mmHg。常见诊断界限会因指南不同而变化。"
            "单次记录不能代表长期情况。"
        )

        self.assertIn("118/76 mmHg", output)
        self.assertIn("单次记录", output)
        self.assertNotIn("诊断界限", output)

    def test_controlled_tool_result_is_saved_as_standard_tool_message(self) -> None:
        runtime = ConversationRuntimeV2(
            settings=self.settings,
            checkpointer=PersistentConversationCheckpointer(Path(self.temp_dir.name) / "controlled-tools.sqlite3"),
            owner_resolver=lambda session_id: self.owners.get(session_id),
            tool_runtime=_FakeToolRuntime(),
        )
        try:
            result = runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message="查询血压")
        finally:
            runtime.close()

        tool_call = next(message for message in result.messages if isinstance(message, AIMessage) and message.tool_calls)
        tool_message = next(message for message in result.messages if isinstance(message, ToolMessage))
        self.assertEqual(tool_call.tool_calls[0]["id"], tool_message.tool_call_id)
        self.assertIn("118/76", result.answer)
        self.assertEqual(result.tool_calls_count, 1)

    def test_health_follow_up_uses_persisted_tool_message_without_another_execution(self) -> None:
        tool_runtime = _FakeToolRuntime()
        runtime = ConversationRuntimeV2(
            settings=self.settings,
            checkpointer=PersistentConversationCheckpointer(Path(self.temp_dir.name) / "follow-up.sqlite3"),
            owner_resolver=lambda session_id: self.owners.get(session_id),
            tool_runtime=tool_runtime,
        )
        try:
            runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message="查询血压")
            answer = runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message="这个数值健康吗？").answer
        finally:
            runtime.close()

        self.assertEqual(tool_runtime.execute_calls, 1)
        self.assertIn("118/76", answer)

    def test_health_tool_result_uses_llm_composer_and_follow_up_reuses_tool_message(self) -> None:
        tool_runtime = _FakeToolRuntime()
        client = _HealthComposerLLMClient()
        settings = Settings(
            CONVERSATION_RUNTIME_V2_ENABLED=True,
            CONVERSATION_RUNTIME_V2_MAX_MESSAGES=10,
            LLM_ENABLED=True,
            LLM_CHAT_ENABLED=True,
        )
        runtime = ConversationRuntimeV2(
            settings=settings,
            checkpointer=PersistentConversationCheckpointer(Path(self.temp_dir.name) / "composer.sqlite3"),
            owner_resolver=lambda session_id: self.owners.get(session_id),
            llm_client=client,
            tool_runtime=tool_runtime,
        )
        try:
            first = runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message="查询血压")
            follow_up = runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message="这个数值健康吗？")
        finally:
            runtime.close()

        self.assertEqual(tool_runtime.execute_calls, 1)
        self.assertIn("118/76", first.answer)
        self.assertIn("118/76", follow_up.answer)
        self.assertEqual(len(client.calls), 3)
        prompts = ["\n".join(message.content for message in call) for call in client.calls]
        self.assertTrue(all("safe result" not in prompt for prompt in prompts))
        self.assertTrue(all("health_data.blood_pressure.summary" not in prompt for prompt in prompts))

    def test_latest_health_request_reexecutes_controlled_tool(self) -> None:
        tool_runtime = _FakeToolRuntime()
        runtime = ConversationRuntimeV2(
            settings=self.settings,
            checkpointer=PersistentConversationCheckpointer(Path(self.temp_dir.name) / "fresh.sqlite3"),
            owner_resolver=lambda session_id: self.owners.get(session_id),
            tool_runtime=tool_runtime,
        )
        try:
            runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message="查询血压")
            runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message="查询最新血压")
        finally:
            runtime.close()

        self.assertEqual(tool_runtime.execute_calls, 2)

    def test_checkpoint_tool_summary_redacts_raw_sensitive_payload(self) -> None:
        safe = safe_tool_result(
            ToolExecutionResult(
                tool_name="documents.query",
                status="completed",
                blocked=False,
                requires_confirmation=False,
                message="completed",
                output_data={
                    "count": 1,
                    "raw_extracted_text": "private long text",
                    "file_path": "C:/private/report.pdf",
                    "token": "secret-token",
                    "summary": {"count": 1},
                },
            )
        )

        encoded = str(safe)
        self.assertNotIn("raw_extracted_text", encoded)
        self.assertNotIn("file_path", encoded)
        self.assertNotIn("secret-token", encoded)

    def test_workflow_uses_v2_even_when_the_legacy_feature_flag_is_disabled(self) -> None:
        v2 = _ConversationResult("v2")
        context = _context(self.owner, self.session_one)

        workflow = ConversationRuntimeWorkflow(
            settings=Settings(CONVERSATION_RUNTIME_V2_ENABLED=False),
            runtime_v2_factory=lambda _: v2,
            display_mirror=lambda *_, **__: None,
        )
        self.assertEqual(workflow.run(context).generated_content, "v2")
        self.assertEqual(v2.calls, 1)

    def test_explicit_record_request_creates_only_a_pending_candidate(self) -> None:
        created = []
        runtime = ConversationRuntimeV2(
            settings=Settings(CONVERSATION_RUNTIME_V2_ENABLED=True, LLM_ENABLED=True, LLM_CHAT_ENABLED=True),
            checkpointer=PersistentConversationCheckpointer(Path(self.temp_dir.name) / "quick-note.sqlite3"),
            owner_resolver=lambda session_id: self.owners.get(session_id),
            llm_client=_QuickNoteLLMClient(),
            draft_candidate_creator=lambda candidate: created.append(candidate) or {"id": "pending-1", "task_type": "quick_note_draft", "status": "pending_confirmation", "draft": candidate},
        )
        try:
            result = runtime.run_turn(session_id=self.session_one, user_id=self.owner, user_message="帮我记录今天头晕")
        finally:
            runtime.close()
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0]["candidate_type"], "symptom")
        self.assertEqual(result.conversation_task["status"], "pending_confirmation")
        self.assertIn("待确认", result.answer)


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
            content='{"type":"final","content":"recorded reply"}',
            provider="test",
            model="test",
            is_mock=True,
        )


class _FailingLLMClient:
    def chat(self, messages, **kwargs):  # noqa: ANN001, ANN003
        raise RuntimeError("provider failure")


class _AssuranceLLMClient:
    def chat(self, messages, **kwargs):  # noqa: ANN001, ANN003
        return LLMResponse(
            content='{"type":"final","content":"你可以放心，肯定没事。"}',
            provider="test",
            model="test",
            is_mock=True,
        )


class _QuickNoteLLMClient:
    def chat(self, messages, **kwargs):  # noqa: ANN001, ANN003
        return LLMResponse(
            content='{"type":"draft_candidate","candidate":{"candidate_type":"symptom","summary":"头晕","occurred_at_hint":"今天","details":"今天有头晕"}}',
            provider="test",
            model="test",
            is_mock=True,
        )


class _HealthComposerLLMClient:
    def __init__(self) -> None:
        self.calls = []

    def chat(self, messages, **kwargs):  # noqa: ANN001, ANN003
        self.calls.append(messages)
        metadata = kwargs.get("metadata") or {}
        if metadata.get("response_composer") == "safe_facts":
            content = "我看了一下这次血压记录，最近一次是118/76 mmHg。可以继续看看近期变化。"
        elif any("已授权工具事实" in str(message.content) for message in messages):
            content = '{"type":"final","content":"刚才那次记录是118/76 mmHg，可以继续看看近期变化。"}'
        else:
            content = '{"type":"tool_call","name":"metric_detail","arguments":{"subject_reference":"self","metric":"blood_pressure","period":"7d"}}'
        return LLMResponse(
            content=content,
            provider="test",
            model="test",
            is_mock=True,
        )


class _FakeToolRuntime:
    def __init__(self) -> None:
        self.execute_calls = 0

    def validate(self, raw):  # noqa: ANN001
        if not isinstance(raw, dict) or raw.get("name") != "metric_detail":
            return None
        return BusinessToolCall(
            id=str(raw.get("id") or "call-blood"),
            name="metric_detail",
            arguments={"subject_reference": "self", "metric": "blood_pressure", "period": "7d"},
        )

    def execute(self, call):  # noqa: ANN001
        self.execute_calls += 1
        result = ToolExecutionResult(
            tool_name="health_data.blood_pressure.summary",
            status="completed",
            blocked=False,
            requires_confirmation=False,
            message="completed",
            output_data={"summary": {"count": 1, "latest_systolic": 118, "latest_diastolic": 76}},
        )
        return BusinessToolExecution(
            tool_message={"capability": "metric_detail", "subject_label": "我", "facts": {"blood_pressure": {"record_count": 1, "latest": "118/76 mmHg"}}, "unavailable_sections": [], "safe_next_actions": []},
            underlying_results=(result,),
            allowed=True,
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
