from __future__ import annotations

import unittest
import uuid

from sqlalchemy import select

from app.db.session import SessionLocal
from app.modules.audit.models import DataAccessLog
from app.modules.permissions import service as permission_service
from tests.api.helpers import (
    add_member,
    auth_headers,
    client,
    create_family,
    create_permission_for_member,
    create_user,
    reset_database,
)


class ApiAccessControlTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.owner = create_user("guard_owner")
        self.member = create_user("guard_member")
        self.family = create_family(self.owner["id"])["family"]
        add_member(self.family["id"], self.owner["id"], self.member["id"], "parent", "Parent")
        create_permission_for_member(self.family["id"], self.member["id"], share_all=True)

    def test_family_profile_allowed_writes_allowed_log(self) -> None:
        response = client.get(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/health-profile",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 200, response.text)
        log = self._latest_log("profile")
        self.assertTrue(log.allowed)
        self.assertEqual(log.permission_result["permission_type"], "profile")

    def test_family_profile_denied_writes_denied_log_without_profile(self) -> None:
        self._update_permission(share_all=False, can_view_profile=False)

        response = client.get(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/health-profile",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(response.json()["detail"]["code"], "permission_denied")
        self.assertNotIn("health_goal", response.text)
        log = self._latest_log("profile")
        self.assertFalse(log.allowed)
        self.assertEqual(log.permission_result["visibility_scope"], "none")

    def test_self_blood_pressure_summary_writes_allowed_log(self) -> None:
        response = client.get(
            "/api/v1/health-data/me/blood-pressure/summary",
            headers=auth_headers(self.member["id"]),
        )

        self.assertEqual(response.status_code, 200, response.text)
        log = self._latest_log("metrics")
        self.assertTrue(log.allowed)
        self.assertEqual(str(log.actor_user_id), self.member["id"])
        self.assertIsNone(log.family_id)

    def test_family_blood_pressure_summary_denied_writes_denied_log(self) -> None:
        self._update_permission(share_all=False, can_view_metrics=False)

        response = client.get(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/health-data/blood-pressure/summary",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 403, response.text)
        self.assertNotIn("latest_record", response.text)
        log = self._latest_log("metrics")
        self.assertFalse(log.allowed)
        self.assertEqual(log.permission_result["permission_type"], "metrics")

    def test_denied_responses_do_not_leak_target_content(self) -> None:
        self._create_family_document("Secret Checkup")
        self._create_family_medical_event("Secret Event")
        self._create_family_report("Secret report summary")
        self._create_family_alert("Secret Alert")
        self._update_permission(
            share_all=False,
            can_view_documents=False,
            can_view_medical_events=False,
            can_view_reports=False,
            can_view_alerts=False,
        )

        checks = [
            (
                f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/documents",
                "Secret Checkup",
            ),
            (
                f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/medical-timeline/events/summary",
                "Secret Event",
            ),
            (
                f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/reports/daily/latest",
                "Secret report summary",
            ),
            (
                f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/alerts/summary",
                "Secret Alert",
            ),
        ]
        for path, secret in checks:
            with self.subTest(path=path):
                response = client.get(path, headers=auth_headers(self.owner["id"]))
                self.assertEqual(response.status_code, 403, response.text)
                self.assertNotIn(secret, response.text)
                self.assertNotIn("file_path", response.text)
                self.assertIn("permission_denied", response.text)

    def _create_family_document(self, title: str) -> None:
        response = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/documents",
            headers=auth_headers(self.owner["id"]),
            json={
                "document_type": "checkup_report",
                "title": title,
                "file_name": "secret.pdf",
                "file_path": "private/secret.pdf",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)

    def _create_family_medical_event(self, title: str) -> None:
        response = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/medical-timeline/events",
            headers=auth_headers(self.owner["id"]),
            json={"event_type": "checkup", "title": title, "summary": "hidden"},
        )
        self.assertEqual(response.status_code, 201, response.text)

    def _create_family_report(self, summary: str) -> None:
        response = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/reports/daily",
            headers=auth_headers(self.owner["id"]),
            json={
                "report_date": "2026-07-04",
                "overall_status": "attention",
                "status_level": "attention",
                "summary_text": summary,
                "generated_by": "user",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)

    def _create_family_alert(self, title: str) -> None:
        response = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/alerts",
            headers=auth_headers(self.owner["id"]),
            json={"alert_type": "medical_follow_up", "level": "info", "title": title, "message": "hidden"},
        )
        self.assertEqual(response.status_code, 201, response.text)

    def _update_permission(self, **updates: bool) -> None:
        with SessionLocal() as db:
            permission_service.update_share_permission(
                db,
                actor_user_id=uuid.UUID(self.owner["id"]),
                family_id=uuid.UUID(self.family["id"]),
                target_user_id=uuid.UUID(self.member["id"]),
                updates=updates,
                reason="access control test",
            )
            db.commit()

    def _latest_log(self, category: str) -> DataAccessLog:
        with SessionLocal() as db:
            log = db.scalars(
                select(DataAccessLog)
                .where(DataAccessLog.data_category == category)
                .order_by(DataAccessLog.created_at.desc())
                .limit(1)
            ).first()
            self.assertIsNotNone(log)
            return log


if __name__ == "__main__":
    unittest.main()
