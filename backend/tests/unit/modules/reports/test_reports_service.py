from __future__ import annotations

import unittest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.modules.identity import service as identity_service
from app.modules.reports import service as reports_service
from app.modules.reports.enums import (
    DailyReportGenerationStatus,
    DailyReportStatusLevel,
)
from app.modules.reports.models import DailyReport


class ReportsServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = SessionLocal()
        suffix = uuid4().hex[:8]
        self.user = identity_service.create_user(
            self.db,
            email=f"phase04c.reports.{suffix}@example.com",
            phone=f"p04c_rep_{suffix}",
            nickname="Reports User",
        )

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()

    def test_save_daily_report_success(self) -> None:
        report = reports_service.save_daily_report(
            self.db,
            user_id=self.user.id,
            report_date=date.today(),
            status_level=DailyReportStatusLevel.ATTENTION,
            summary_text="用户传入的日报摘要",
        )

        self.assertEqual(report.summary_text, "用户传入的日报摘要")

    def test_save_daily_report_upserts_same_user_and_date(self) -> None:
        report_date = date.today()
        first = reports_service.save_daily_report(
            self.db,
            user_id=self.user.id,
            report_date=report_date,
            status_level=DailyReportStatusLevel.ATTENTION,
            summary_text="第一次",
        )
        second = reports_service.save_daily_report(
            self.db,
            user_id=self.user.id,
            report_date=report_date,
            status_level=DailyReportStatusLevel.FOLLOW_UP,
            summary_text="第二次",
        )

        count = self.db.scalar(
            select(func.count())
            .select_from(DailyReport)
            .where(DailyReport.user_id == self.user.id),
        )

        self.assertEqual(first.id, second.id)
        self.assertEqual(second.summary_text, "第二次")
        self.assertEqual(count, 1)

    def test_latest_daily_report_returns_latest_date(self) -> None:
        reports_service.save_daily_report(
            self.db,
            user_id=self.user.id,
            report_date=date.today() - timedelta(days=1),
            status_level=DailyReportStatusLevel.ATTENTION,
        )
        latest = reports_service.save_daily_report(
            self.db,
            user_id=self.user.id,
            report_date=date.today(),
            status_level=DailyReportStatusLevel.FOLLOW_UP,
        )

        result = reports_service.get_latest_daily_report(self.db, user_id=self.user.id)

        self.assertEqual(result.id, latest.id)

    def test_no_report_snapshot_does_not_claim_health_ok(self) -> None:
        snapshot = reports_service.get_daily_report_snapshot(self.db, user_id=self.user.id)

        self.assertFalse(snapshot.has_report)
        self.assertEqual(snapshot.message, "系统内暂无日报记录")
        self.assertNotIn("身体没问题", snapshot.message)

    def test_mark_daily_report_failed(self) -> None:
        failed = reports_service.mark_daily_report_failed(
            self.db,
            user_id=self.user.id,
            report_date=date.today(),
        )

        self.assertEqual(failed.generation_status, DailyReportGenerationStatus.FAILED)


if __name__ == "__main__":
    unittest.main()
