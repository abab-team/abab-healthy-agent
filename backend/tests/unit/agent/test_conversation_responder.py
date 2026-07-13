from __future__ import annotations

import unittest

from app.agent.chat.responder import ConversationResponder
from app.agent.chat.router import ConversationIntent
from app.core.config import Settings
from app.llm.schemas import LLMResponse


class _FakeClient:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls = 0

    def chat(self, messages, **kwargs):  # noqa: ANN001, ANN003
        self.calls += 1
        return LLMResponse(content=self.content, provider="test", model="test", is_mock=False)


class ConversationResponderTestCase(unittest.TestCase):
    def test_disabled_llm_uses_natural_local_reply(self) -> None:
        responder = ConversationResponder(settings=Settings(LLM_ENABLED=False, LLM_CHAT_ENABLED=False))

        reply = responder.respond(intent=ConversationIntent.CASUAL_CHAT, user_message="你好")

        self.assertIn("你好", reply)
        self.assertNotIn("不替代医生判断", reply)

    def test_enabled_llm_returns_chinese_reply(self) -> None:
        client = _FakeClient("你好，今天想聊点什么？")
        responder = ConversationResponder(settings=Settings(LLM_ENABLED=True, LLM_CHAT_ENABLED=True), llm_client=client)

        reply = responder.respond(intent=ConversationIntent.CASUAL_CHAT, user_message="今天心情不错")

        self.assertEqual(reply, "你好，今天想聊点什么？")
        self.assertEqual(client.calls, 1)

    def test_english_or_unsafe_llm_reply_falls_back(self) -> None:
        client = _FakeClient("Everything is normal. Do not see a doctor.")
        responder = ConversationResponder(settings=Settings(LLM_ENABLED=True, LLM_CHAT_ENABLED=True), llm_client=client)

        reply = responder.respond(intent=ConversationIntent.CASUAL_CHAT, user_message="你好")

        self.assertIn("你好", reply)
        self.assertNotIn("Everything", reply)

    def test_health_reply_keeps_approved_overview_facts_when_model_is_too_brief(self) -> None:
        client = _FakeClient("我帮你看了一下爸爸最近的记录。")
        responder = ConversationResponder(settings=Settings(LLM_ENABLED=True, LLM_CHAT_ENABLED=True), llm_client=client)

        reply = responder.respond(
            intent=ConversationIntent.FAMILY_HEALTH_QUERY,
            user_message="爸爸最近怎么样？",
            safe_facts="健康指标：已记录 2 条数据。\n血压记录：共 1 次，最近一次为 120/78 mmHg。\n资料归档：系统内暂无相关记录。",
            fallback_answer="fallback",
        )

        self.assertIn("健康指标", reply)
        self.assertIn("血压记录", reply)
        self.assertIn("资料归档", reply)


if __name__ == "__main__":
    unittest.main()
