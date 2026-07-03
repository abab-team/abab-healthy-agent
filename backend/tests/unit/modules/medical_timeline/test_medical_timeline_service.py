from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from app.db.session import SessionLocal
from app.modules.identity import service as identity_service
from app.modules.medical_timeline import service as medical_service
from app.modules.medical_timeline.enums import MedicalEventStatus, MedicalEventType


class MedicalTimelineServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = SessionLocal()
        suffix = uuid4().hex[:8]
        self.user = identity_service.create_user(
            self.db,
            email=f"phase04c.medical.{suffix}@example.com",
            phone=f"p04c_med_{suffix}",
            nickname="Medical User",
        )

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()

    def test_create_medical_event_success(self) -> None:
        event = medical_service.create_medical_event(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            event_type=MedicalEventType.CHECKUP,
            title="年度体检记录",
        )

        self.assertEqual(event.title, "年度体检记录")
        self.assertEqual(event.event_type, MedicalEventType.CHECKUP)

    def test_empty_diagnosis_is_not_generated(self) -> None:
        event = medical_service.create_medical_event(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            event_type=MedicalEventType.OTHER,
            title="用户手动记录",
            summary="用户确认的资料摘要",
        )

        self.assertIsNone(event.diagnosis_text)

    def test_get_medical_timeline_returns_events(self) -> None:
        event = medical_service.create_medical_event(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            event_type=MedicalEventType.LAB_TEST,
            title="化验单",
            event_date=date.today(),
        )

        events = medical_service.get_medical_timeline(
            self.db,
            user_id=self.user.id,
        )

        self.assertEqual(events[0].id, event.id)

    def test_get_follow_up_events_returns_follow_up_items(self) -> None:
        follow_up_at = datetime.now(timezone.utc) + timedelta(days=1)
        medical_service.create_medical_event(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            event_type=MedicalEventType.FOLLOW_UP,
            title="复查提醒",
            follow_up_needed=True,
            follow_up_at=follow_up_at,
        )

        events = medical_service.get_follow_up_events(
            self.db,
            user_id=self.user.id,
        )

        self.assertEqual(len(events), 1)
        self.assertTrue(events[0].follow_up_needed)

    def test_archive_medical_event(self) -> None:
        event = medical_service.create_medical_event(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            event_type=MedicalEventType.OTHER,
            title="待归档事件",
        )

        archived = medical_service.archive_medical_event(self.db, event.id)

        self.assertEqual(archived.status, MedicalEventStatus.ARCHIVED)


if __name__ == "__main__":
    unittest.main()
