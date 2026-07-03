from __future__ import annotations

import unittest

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.modules.health_data.models import BloodPressureRecord
from app.modules.health_record import service as health_record_service
from app.modules.health_record.enums import HealthRecordDraftStatus, SymptomRecordStatus
from app.modules.health_record.exceptions import (
    HealthRecordDraftNotPendingError,
    InvalidHealthRecordDraftError,
)
from app.modules.health_record.models import HealthRecordDraft, SymptomRecord
from app.modules.identity import service as identity_service


class HealthRecordServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = SessionLocal()
        self.user = identity_service.create_user(
            self.db,
            email="phase04b.health_record.user@example.com",
            phone="p04b_record_user",
            nickname="Health Record User",
        )

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()

    def test_create_symptom_record_success(self) -> None:
        record = health_record_service.create_symptom_record(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            raw_text="今天头痛两小时",
            symptom_name="头痛",
            follow_up_needed=True,
        )

        self.assertEqual(record.user_id, self.user.id)
        self.assertEqual(record.symptom_name, "头痛")
        self.assertTrue(record.follow_up_needed)

    def test_create_symptom_record_requires_raw_text(self) -> None:
        with self.assertRaises(InvalidHealthRecordDraftError):
            health_record_service.create_symptom_record(
                self.db,
                user_id=self.user.id,
                created_by_user_id=self.user.id,
                raw_text=" ",
            )

    def test_recent_symptoms_and_summary(self) -> None:
        health_record_service.create_symptom_record(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            raw_text="最近咳嗽",
            symptom_name="咳嗽",
            follow_up_needed=True,
        )

        records = health_record_service.get_recent_symptoms(
            self.db,
            user_id=self.user.id,
        )
        summary = health_record_service.get_symptom_summary(
            self.db,
            user_id=self.user.id,
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(summary.count, 1)
        self.assertEqual(summary.active_count, 1)
        self.assertEqual(summary.follow_up_needed_count, 1)
        self.assertFalse(hasattr(summary, "diagnosis"))

    def test_confirm_symptom_draft_creates_symptom_record(self) -> None:
        draft = health_record_service.create_health_record_draft(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            raw_text="昨晚胃痛，持续半小时",
            extracted_json={
                "symptom": {
                    "symptom_name": "胃痛",
                    "body_part": "腹部",
                    "duration_text": "半小时",
                    "follow_up_needed": True,
                    "ai_summary": "用户确认前的结构化草稿",
                },
            },
        )

        record = health_record_service.confirm_symptom_draft(
            self.db,
            draft_id=draft.id,
            confirmed_by_user_id=self.user.id,
        )
        refreshed_draft = self.db.get(HealthRecordDraft, draft.id)

        self.assertEqual(record.symptom_name, "胃痛")
        self.assertEqual(record.source.value, "ai_extracted")
        self.assertEqual(refreshed_draft.status, HealthRecordDraftStatus.CONFIRMED)
        self.assertEqual(refreshed_draft.confirmed_record_id, record.id)

    def test_confirmed_draft_cannot_be_confirmed_twice(self) -> None:
        draft = health_record_service.create_health_record_draft(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            raw_text="头晕",
            extracted_json={"symptom_name": "头晕"},
        )
        health_record_service.confirm_symptom_draft(
            self.db,
            draft_id=draft.id,
            confirmed_by_user_id=self.user.id,
        )

        with self.assertRaises(HealthRecordDraftNotPendingError):
            health_record_service.confirm_symptom_draft(
                self.db,
                draft_id=draft.id,
                confirmed_by_user_id=self.user.id,
            )

    def test_cancelled_draft_cannot_be_confirmed(self) -> None:
        draft = health_record_service.create_health_record_draft(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            raw_text="乏力",
            extracted_json={"symptom_name": "乏力"},
        )
        health_record_service.cancel_draft(self.db, draft.id)

        with self.assertRaises(HealthRecordDraftNotPendingError):
            health_record_service.confirm_symptom_draft(
                self.db,
                draft_id=draft.id,
                confirmed_by_user_id=self.user.id,
            )

    def test_update_symptom_status(self) -> None:
        record = health_record_service.create_symptom_record(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            raw_text="皮肤瘙痒",
            symptom_name="瘙痒",
        )

        updated = health_record_service.update_symptom_record_status(
            self.db,
            record.id,
            SymptomRecordStatus.RESOLVED,
        )

        self.assertEqual(updated.status, SymptomRecordStatus.RESOLVED)

    def test_draft_confirmation_does_not_write_blood_pressure(self) -> None:
        draft = health_record_service.create_health_record_draft(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            raw_text="血压 120/80，今天有点头痛",
            extracted_json={"symptom_name": "头痛"},
        )
        health_record_service.confirm_symptom_draft(
            self.db,
            draft_id=draft.id,
            confirmed_by_user_id=self.user.id,
        )

        symptom_count = self.db.scalar(
            select(func.count())
            .select_from(SymptomRecord)
            .where(SymptomRecord.user_id == self.user.id),
        )
        pressure_count = self.db.scalar(
            select(func.count())
            .select_from(BloodPressureRecord)
            .where(BloodPressureRecord.user_id == self.user.id),
        )

        self.assertEqual(symptom_count, 1)
        self.assertEqual(pressure_count, 0)


if __name__ == "__main__":
    unittest.main()
