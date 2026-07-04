from __future__ import annotations

import unittest
from uuid import uuid4

from app.db.session import SessionLocal
from app.modules.audit import service


class AuditServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = SessionLocal()
        self.actor_user_id = uuid4()
        self.target_user_id = uuid4()
        self.family_id = uuid4()

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()

    def test_log_allowed_data_access(self) -> None:
        log = service.log_data_access(
            self.db,
            actor_user_id=self.actor_user_id,
            target_user_id=self.target_user_id,
            family_id=self.family_id,
            data_category="metrics",
            action="view",
            access_reason="unit_allowed",
            allowed=True,
            permission_result={
                "allowed": True,
                "permission_type": "metrics",
                "action": "view",
                "reason": "family_share_all",
                "visibility_scope": "family_member_shared",
                "raw_text": "should not be saved",
            },
        )

        self.assertTrue(log.allowed)
        self.assertEqual(log.permission_result["permission_type"], "metrics")
        self.assertNotIn("raw_text", log.permission_result)

    def test_log_denied_data_access(self) -> None:
        log = service.log_data_access(
            self.db,
            actor_user_id=self.actor_user_id,
            target_user_id=self.target_user_id,
            family_id=self.family_id,
            data_category="documents",
            action="view",
            access_reason="unit_denied",
            allowed=False,
            permission_result={
                "allowed": False,
                "permission_type": "documents",
                "action": "view",
                "reason": "documents_not_shared",
                "visibility_scope": "none",
                "file_path": "private/report.pdf",
            },
        )

        self.assertFalse(log.allowed)
        self.assertNotIn("file_path", log.permission_result)

    def test_list_data_access_logs_filters(self) -> None:
        service.log_data_access(
            self.db,
            actor_user_id=self.actor_user_id,
            target_user_id=self.target_user_id,
            family_id=self.family_id,
            data_category="alerts",
            action="view",
            allowed=True,
        )
        service.log_data_access(
            self.db,
            actor_user_id=uuid4(),
            target_user_id=self.target_user_id,
            family_id=self.family_id,
            data_category="reports",
            action="view",
            allowed=False,
        )

        logs = service.list_data_access_logs(
            self.db,
            actor_user_id=self.actor_user_id,
            family_id=self.family_id,
            data_category="alerts",
            allowed=True,
        )

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].data_category, "alerts")


if __name__ == "__main__":
    unittest.main()
