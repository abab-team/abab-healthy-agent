from __future__ import annotations

import unittest
from datetime import date

from app.agent.chat.time_range_parser import parse_time_range


class ChatTimeRangeParserTestCase(unittest.TestCase):
    def test_parse_recent_days(self) -> None:
        parsed = parse_time_range("最近 14 天的睡眠", reference_date=date(2026, 7, 8))

        self.assertEqual(parsed.days, 14)
        self.assertEqual(parsed.start_date, date(2026, 6, 25))
        self.assertEqual(parsed.end_date, date(2026, 7, 8))

    def test_parse_today_and_yesterday(self) -> None:
        today = parse_time_range("今天血压", reference_date=date(2026, 7, 8))
        yesterday = parse_time_range("昨天提醒", reference_date=date(2026, 7, 8))

        self.assertEqual(today.days, 1)
        self.assertEqual(today.start_date, date(2026, 7, 8))
        self.assertEqual(yesterday.start_date, date(2026, 7, 7))
        self.assertEqual(yesterday.end_date, date(2026, 7, 7))

    def test_parse_this_month_and_last_month(self) -> None:
        this_month = parse_time_range("这个月健康情况", reference_date=date(2026, 7, 8))
        last_month = parse_time_range("上个月症状", reference_date=date(2026, 7, 8))

        self.assertEqual(this_month.start_date, date(2026, 7, 1))
        self.assertEqual(this_month.end_date, date(2026, 7, 8))
        self.assertEqual(last_month.start_date, date(2026, 6, 1))
        self.assertEqual(last_month.end_date, date(2026, 6, 30))

    def test_default_is_last_seven_days(self) -> None:
        parsed = parse_time_range("健康情况", reference_date=date(2026, 7, 8))

        self.assertEqual(parsed.days, 7)
        self.assertEqual(parsed.start_date, date(2026, 7, 2))
        self.assertEqual(parsed.end_date, date(2026, 7, 8))


if __name__ == "__main__":
    unittest.main()
