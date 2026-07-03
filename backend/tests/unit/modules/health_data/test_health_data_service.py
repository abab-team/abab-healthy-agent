from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.modules.health_data import service as health_data_service
from app.modules.health_data.enums import MetricType
from app.modules.health_data.exceptions import (
    InvalidBloodPressureValueError,
    InvalidMetricValueError,
)
from app.modules.health_data.models import BloodPressureRecord, HealthMetric
from app.modules.identity import service as identity_service


class HealthDataServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = SessionLocal()
        self.user = identity_service.create_user(
            self.db,
            email="phase04b.health_data.user@example.com",
            phone="p04b_data_user",
            nickname="Health Data User",
        )

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()

    def test_add_metric_and_recent_metrics(self) -> None:
        metric = health_data_service.add_metric(
            self.db,
            user_id=self.user.id,
            metric_type=MetricType.STEPS,
            value_numeric=8000,
            unit="steps",
        )

        records = health_data_service.get_recent_metrics(
            self.db,
            user_id=self.user.id,
            metric_types=[MetricType.STEPS],
        )

        self.assertEqual(metric.metric_type, MetricType.STEPS)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].id, metric.id)

    def test_add_metric_requires_value(self) -> None:
        with self.assertRaises(InvalidMetricValueError):
            health_data_service.add_metric(
                self.db,
                user_id=self.user.id,
                metric_type=MetricType.SLEEP_DURATION,
            )

    def test_metric_summary_reports_data_quality_without_health_judgment(self) -> None:
        now = datetime.now(timezone.utc)
        health_data_service.add_metric(
            self.db,
            user_id=self.user.id,
            metric_type=MetricType.SLEEP_DURATION,
            value_numeric=6,
            unit="hour",
            measured_at=now - timedelta(days=2),
        )
        health_data_service.add_metric(
            self.db,
            user_id=self.user.id,
            metric_type=MetricType.SLEEP_DURATION,
            value_numeric=7,
            unit="hour",
            measured_at=now - timedelta(days=1),
        )
        health_data_service.add_metric(
            self.db,
            user_id=self.user.id,
            metric_type=MetricType.SLEEP_DURATION,
            value_numeric=8,
            unit="hour",
            measured_at=now,
        )

        summary = health_data_service.get_metric_summary(
            self.db,
            user_id=self.user.id,
            metric_type=MetricType.SLEEP_DURATION,
        )

        self.assertEqual(summary.count, 3)
        self.assertEqual(summary.latest_value, 8.0)
        self.assertEqual(summary.avg_value, 7.0)
        self.assertEqual(summary.data_quality, "partial")
        self.assertFalse(hasattr(summary, "diagnosis"))
        self.assertFalse(hasattr(summary, "risk_level"))

    def test_add_blood_pressure_record_and_summary(self) -> None:
        record = health_data_service.add_blood_pressure_record(
            self.db,
            user_id=self.user.id,
            systolic=120,
            diastolic=80,
            pulse=72,
        )

        summary = health_data_service.get_blood_pressure_summary(
            self.db,
            user_id=self.user.id,
        )

        self.assertEqual(record.systolic, 120)
        self.assertEqual(summary.count, 1)
        self.assertEqual(summary.latest_systolic, 120)
        self.assertEqual(summary.latest_diastolic, 80)
        self.assertEqual(summary.data_quality, "insufficient")
        self.assertFalse(hasattr(summary, "diagnosis"))
        self.assertFalse(hasattr(summary, "risk_level"))

    def test_unreasonable_blood_pressure_value_is_rejected(self) -> None:
        with self.assertRaises(InvalidBloodPressureValueError):
            health_data_service.add_blood_pressure_record(
                self.db,
                user_id=self.user.id,
                systolic=20,
                diastolic=80,
            )

    def test_empty_blood_pressure_summary_means_missing_data_only(self) -> None:
        summary = health_data_service.get_blood_pressure_summary(
            self.db,
            user_id=self.user.id,
        )

        self.assertEqual(summary.count, 0)
        self.assertEqual(summary.data_quality, "missing")
        self.assertIsNone(summary.latest_systolic)
        self.assertFalse(hasattr(summary, "health_status"))

    def test_blood_pressure_does_not_write_health_metrics(self) -> None:
        health_data_service.add_blood_pressure_record(
            self.db,
            user_id=self.user.id,
            systolic=118,
            diastolic=76,
        )

        metric_count = self.db.scalar(
            select(func.count())
            .select_from(HealthMetric)
            .where(HealthMetric.user_id == self.user.id),
        )
        pressure_count = self.db.scalar(
            select(func.count())
            .select_from(BloodPressureRecord)
            .where(BloodPressureRecord.user_id == self.user.id),
        )

        self.assertEqual(metric_count, 0)
        self.assertEqual(pressure_count, 1)


if __name__ == "__main__":
    unittest.main()
