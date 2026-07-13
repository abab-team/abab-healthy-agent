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


    def test_identity_uses_controlled_context_without_calling_the_model(self) -> None:
        client = _FakeClient("\u4e0d\u5e94\u8be5\u8c03\u7528")
        responder = ConversationResponder(settings=Settings(LLM_ENABLED=True, LLM_CHAT_ENABLED=True), llm_client=client)

        reply = responder.respond(
            intent=ConversationIntent.CASUAL_CHAT,
            user_message="\u6211\u662f\u8c01",
            assistant_context=("\u5f53\u524d\u7528\u6237\u79f0\u547c: Gala",),
        )

        self.assertIn("Gala", reply)
        self.assertEqual(client.calls, 0)

    def test_continuity_and_numeric_interpretation_have_safe_local_replies(self) -> None:
        client = _FakeClient("\u4e0d\u5e94\u8be5\u8c03\u7528")
        responder = ConversationResponder(settings=Settings(LLM_ENABLED=True, LLM_CHAT_ENABLED=True), llm_client=client)

        continuity = responder.respond(intent=ConversationIntent.CASUAL_CHAT, user_message="\u4f60\u4e0d\u662f\u8bfb\u8fc7\u4e86\u5417")
        interpretation = responder.respond(intent=ConversationIntent.HEALTH_KNOWLEDGE, user_message="\u8fd9\u4e2a\u6570\u503c\u5065\u5eb7\u5417")

        self.assertIn("\u8bb0\u5f97", continuity)
        self.assertIn("\u5177\u4f53\u6570\u503c", interpretation)
        self.assertIn("\u8d8b\u52bf", interpretation)
        self.assertEqual(client.calls, 0)

    def test_explicit_blood_pressure_value_gets_safe_reference_explanation(self) -> None:
        client = _FakeClient("\u4e0d\u5e94\u8be5\u8c03\u7528")
        responder = ConversationResponder(settings=Settings(LLM_ENABLED=True, LLM_CHAT_ENABLED=True), llm_client=client)

        reply = responder.respond(intent=ConversationIntent.HEALTH_KNOWLEDGE, user_message="118/76\u5065\u5eb7\u5417\uff1f")

        self.assertIn("118/76", reply)
        self.assertIn("\u5e38\u89c1\u6210\u4eba\u9759\u606f\u8840\u538b\u53c2\u8003\u533a\u95f4", reply)
        self.assertIn("\u8d8b\u52bf", reply)
        self.assertNotIn("\u8bca\u65ad", reply)
        self.assertNotIn("\u5904\u65b9", reply)
        self.assertNotIn("\u5242\u91cf", reply)
        self.assertNotIn("\u505c\u836f", reply)
        self.assertEqual(client.calls, 0)


if __name__ == "__main__":
    unittest.main()
