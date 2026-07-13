from __future__ import annotations

import unittest

from app.agent.chat import ConversationIntent, SuggestedAction, parse_health_query, route_conversation


class ConversationRouterTestCase(unittest.TestCase):
    def test_routes_small_talk_without_a_tool(self) -> None:
        route = route_conversation("今天心情不错", parse_health_query("今天心情不错"))
        self.assertEqual(route.intent, ConversationIntent.CASUAL_CHAT)

    def test_routes_record_query_to_controlled_path(self) -> None:
        route = route_conversation("我最近睡眠怎么样？", parse_health_query("我最近睡眠怎么样？"))
        self.assertEqual(route.intent, ConversationIntent.HEALTH_RECORD_QUERY)

    def test_routes_family_query_to_controlled_family_path(self) -> None:
        route = route_conversation("爸爸最近血压怎么样？", parse_health_query("爸爸最近血压怎么样？"))
        self.assertEqual(route.intent, ConversationIntent.FAMILY_HEALTH_QUERY)

    def test_routes_realtime_external_question_without_a_health_tool(self) -> None:
        route = route_conversation("上海天气怎么样？", parse_health_query("上海天气怎么样？"))
        self.assertEqual(route.intent, ConversationIntent.OTHER)

    def test_routes_general_health_knowledge_without_personal_query(self) -> None:
        route = route_conversation("为什么会睡不好？", parse_health_query("为什么会睡不好？"))
        self.assertEqual(route.intent, ConversationIntent.HEALTH_KNOWLEDGE)

    def test_routes_write_request_to_a_confirmed_draft_entry(self) -> None:
        route = route_conversation("帮我记录今天头痛", parse_health_query("帮我记录今天头痛"))
        self.assertEqual(route.intent, ConversationIntent.WRITE_REQUEST)
        self.assertEqual(route.suggested_action, SuggestedAction.SYMPTOM_DRAFT)


    def test_routes_numeric_health_interpretation_to_safe_knowledge_reply(self) -> None:
        route = route_conversation("\u8fd9\u4e2a\u6570\u503c\u5065\u5eb7\u5417", parse_health_query("\u8fd9\u4e2a\u6570\u503c\u5065\u5eb7\u5417"))

        self.assertEqual(route.intent, ConversationIntent.HEALTH_KNOWLEDGE)


if __name__ == "__main__":
    unittest.main()
