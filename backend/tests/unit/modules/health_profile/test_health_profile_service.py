from __future__ import annotations

import unittest

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.modules.health_profile import service as health_profile_service
from app.modules.health_profile.models import HealthProfile
from app.modules.identity import service as identity_service


class HealthProfileServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = SessionLocal()
        self.user = identity_service.create_user(
            self.db,
            email="phase04b.profile.user@example.com",
            phone="p04b_profile_user",
            nickname="Profile User",
        )

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()

    def test_ensure_profile_creates_empty_profile(self) -> None:
        profile = health_profile_service.ensure_profile(self.db, self.user.id)

        self.assertEqual(profile.user_id, self.user.id)
        self.assertIsNone(profile.health_goal)

    def test_create_or_update_profile_updates_goal(self) -> None:
        profile = health_profile_service.create_or_update_profile(
            self.db,
            self.user.id,
            {"health_goal": "保持规律睡眠"},
        )

        self.assertEqual(profile.health_goal, "保持规律睡眠")

        updated = health_profile_service.create_or_update_profile(
            self.db,
            self.user.id,
            {"health_goal": "每周步行三次"},
        )

        self.assertEqual(updated.id, profile.id)
        self.assertEqual(updated.health_goal, "每周步行三次")

    def test_ensure_profile_is_idempotent(self) -> None:
        first = health_profile_service.ensure_profile(self.db, self.user.id)
        second = health_profile_service.ensure_profile(self.db, self.user.id)

        count = self.db.scalar(
            select(func.count())
            .select_from(HealthProfile)
            .where(HealthProfile.user_id == self.user.id),
        )

        self.assertEqual(first.id, second.id)
        self.assertEqual(count, 1)

    def test_profile_snapshot_excludes_identity_sensitive_fields(self) -> None:
        snapshot = health_profile_service.get_profile_snapshot(self.db, self.user.id)

        self.assertEqual(snapshot.user_id, self.user.id)
        self.assertFalse(hasattr(snapshot, "email"))
        self.assertFalse(hasattr(snapshot, "phone"))
        self.assertFalse(hasattr(snapshot, "password_hash"))


if __name__ == "__main__":
    unittest.main()
