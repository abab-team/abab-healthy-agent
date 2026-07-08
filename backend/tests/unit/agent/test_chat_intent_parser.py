from __future__ import annotations

import unittest
from datetime import date

from app.agent.chat import HealthQueryIntent, parse_health_query


class ChatIntentParserTestCase(unittest.TestCase):
    def test_parse_blood_pressure_query(self) -> None:
        plan = parse_health_query("最近一周我的血压记录怎么样？", reference_date=date(2026, 7, 8))

        self.assertEqual(plan.intent, HealthQueryIntent.QUERY_BLOOD_PRESSURE)
        self.assertEqual(plan.tool_name, "health_data.blood_pressure.summary")
        self.assertEqual(plan.tool_input["days"], 7)

    def test_parse_metric_average_query(self) -> None:
        plan = parse_health_query("我最近 30 天平均睡眠怎么样？", reference_date=date(2026, 7, 8))

        self.assertEqual(plan.intent, HealthQueryIntent.QUERY_METRICS)
        self.assertEqual(plan.metric_type, "sleep_duration")
        self.assertEqual(plan.aggregation, "avg")
        self.assertEqual(plan.tool_name, "health_data.metric.summary")

    def test_parse_symptoms_documents_alerts_and_daily_status(self) -> None:
        cases = [
            ("最近有什么症状记录？", HealthQueryIntent.QUERY_SYMPTOMS, "health_record.symptoms.query"),
            ("系统内有哪些报告文档？", HealthQueryIntent.QUERY_DOCUMENTS, "documents.query"),
            ("今天有哪些待办提醒？", HealthQueryIntent.QUERY_ALERTS, "alerts.query"),
            ("帮我总结最近健康情况", HealthQueryIntent.QUERY_DAILY_STATUS, "health_data.metrics.recent"),
        ]

        for message, intent, tool_name in cases:
            with self.subTest(message=message):
                plan = parse_health_query(message, reference_date=date(2026, 7, 8))
                self.assertEqual(plan.intent, intent)
                self.assertEqual(plan.tool_name, tool_name)

    def test_member_label_is_informational_only(self) -> None:
        plan = parse_health_query("看看爸爸最近一周的血压", reference_date=date(2026, 7, 8))

        self.assertEqual(plan.member_label, "爸爸")
        self.assertEqual(plan.member_scope, "family")
        self.assertEqual(plan.tool_input["days"], 7)

    def test_unknown_query_is_safe_unknown(self) -> None:
        plan = parse_health_query("帮我讲个笑话")

        self.assertTrue(plan.is_unknown)
        self.assertIsNone(plan.tool_name)
        self.assertEqual(plan.safe_unknown_reason, "unsupported_health_query_intent")


if __name__ == "__main__":
    unittest.main()
