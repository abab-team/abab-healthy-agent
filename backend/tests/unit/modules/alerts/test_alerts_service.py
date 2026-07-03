from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.db.session import SessionLocal
from app.modules.alerts import repository as alert_repository
from app.modules.alerts import service as alert_service
from app.modules.alerts.enums import AlertLevel, AlertStatus, AlertType
from app.modules.alerts.exceptions import InvalidAlertTransitionError
from app.modules.identity import service as identity_service


class AlertsServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = SessionLocal()
        suffix = uuid4().hex[:8]
        self.user = identity_service.create_user(
            self.db,
            email=f"phase04c.alerts.{suffix}@example.com",
            phone=f"p04c_alt_{suffix}",
            nickname="Alerts User",
        )

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()

    def _create_alert(self, *, due_at=None):
        return alert_service.create_alert(
            self.db,
            user_id=self.user.id,
            alert_type=AlertType.DOCUMENT_REVIEW,
            level=AlertLevel.ATTENTION,
            title="资料待确认",
            message="有一条资料需要用户确认",
            due_at=due_at,
        )

    def test_create_alert_success(self) -> None:
        alert = self._create_alert()

        self.assertEqual(alert.status, AlertStatus.ACTIVE)

    def test_get_active_alerts_returns_only_active_status(self) -> None:
        alert = self._create_alert()
        alert_service.mark_alert_read(self.db, alert.id, actor_user_id=self.user.id)

        alerts = alert_service.get_active_alerts(self.db, user_id=self.user.id)

        self.assertEqual(alerts, [])

    def test_mark_alert_read_creates_event(self) -> None:
        alert = self._create_alert()

        updated = alert_service.mark_alert_read(
            self.db,
            alert.id,
            actor_user_id=self.user.id,
        )
        events = alert_repository.list_alert_events(self.db, alert.id)

        self.assertEqual(updated.status, AlertStatus.READ)
        self.assertEqual(events[-1].after_status, AlertStatus.READ)

    def test_resolve_alert_creates_event_and_resolved_at(self) -> None:
        alert = self._create_alert()

        resolved = alert_service.resolve_alert(
            self.db,
            alert.id,
            actor_user_id=self.user.id,
            note="用户已处理",
        )
        events = alert_repository.list_alert_events(self.db, alert.id)

        self.assertEqual(resolved.status, AlertStatus.RESOLVED)
        self.assertIsNotNone(resolved.resolved_at)
        self.assertEqual(events[-1].after_status, AlertStatus.RESOLVED)

    def test_dismiss_and_reopen_alert(self) -> None:
        alert = self._create_alert()
        dismissed = alert_service.dismiss_alert(self.db, alert.id, actor_user_id=self.user.id)
        reopened = alert_service.reopen_alert(self.db, alert.id, actor_user_id=self.user.id)

        self.assertEqual(dismissed.status, AlertStatus.ACTIVE)
        self.assertEqual(reopened.status, AlertStatus.ACTIVE)

    def test_invalid_transition_raises(self) -> None:
        alert = self._create_alert()
        alert_service.resolve_alert(self.db, alert.id, actor_user_id=self.user.id)

        with self.assertRaises(InvalidAlertTransitionError):
            alert_service.mark_alert_read(self.db, alert.id, actor_user_id=self.user.id)

    def test_alert_summary_does_not_claim_health_ok(self) -> None:
        summary = alert_service.get_alert_summary(self.db, user_id=self.user.id)

        self.assertEqual(summary.active_count, 0)
        self.assertEqual(summary.message, "系统内暂无 active 提醒记录")
        self.assertNotIn("身体没问题", summary.message)

    def test_get_due_alerts(self) -> None:
        self._create_alert(due_at=datetime.now(timezone.utc) - timedelta(hours=1))

        due_alerts = alert_service.get_due_alerts(self.db, user_id=self.user.id)

        self.assertEqual(len(due_alerts), 1)


if __name__ == "__main__":
    unittest.main()
