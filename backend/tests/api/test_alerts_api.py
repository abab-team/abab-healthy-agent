from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.modules.alerts.models import AlertEvent
from tests.api.helpers import (
    SessionLocal,
    add_member,
    auth_headers,
    client,
    create_family,
    create_permission_for_member,
    create_user,
    reset_database,
)


class AlertsApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.owner = create_user("alert_owner")
        self.member = create_user("alert_member")
        self.family = create_family(self.owner["id"])["family"]
        add_member(self.family["id"], self.owner["id"], self.member["id"], "parent", "Parent")

    def test_create_get_summary_due_and_transitions(self) -> None:
        alert = self._post_my_alert(due_at=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()).json()
        active = client.get("/api/v1/alerts/me/active", headers=auth_headers(self.owner["id"]))
        due = client.get("/api/v1/alerts/me/due", headers=auth_headers(self.owner["id"]))
        summary = client.get("/api/v1/alerts/me/summary", headers=auth_headers(self.owner["id"]))
        read = client.post(f"/api/v1/alerts/me/{alert['id']}/read", headers=auth_headers(self.owner["id"]))
        resolved = client.post(f"/api/v1/alerts/me/{alert['id']}/resolve", headers=auth_headers(self.owner["id"]))
        reopened = client.post(f"/api/v1/alerts/me/{alert['id']}/reopen", headers=auth_headers(self.owner["id"]))
        dismissed = client.post(f"/api/v1/alerts/me/{alert['id']}/dismiss", headers=auth_headers(self.owner["id"]))

        self.assertEqual(len(active.json()["items"]), 1)
        self.assertEqual(len(due.json()["items"]), 1)
        self.assertEqual(summary.json()["active_count"], 1)
        self.assertEqual(read.json()["status"], "read")
        self.assertEqual(resolved.json()["status"], "resolved")
        self.assertEqual(reopened.json()["status"], "active")
        self.assertEqual(dismissed.json()["status"], "dismissed")
        self.assertGreaterEqual(self._alert_event_count(), 5)

    def test_invalid_transition_returns_conflict(self) -> None:
        alert = self._post_my_alert().json()
        client.post(f"/api/v1/alerts/me/{alert['id']}/resolve", headers=auth_headers(self.owner["id"]))
        response = client.post(f"/api/v1/alerts/me/{alert['id']}/read", headers=auth_headers(self.owner["id"]))

        self.assertEqual(response.status_code, 409)

    def test_summary_does_not_output_diagnosis(self) -> None:
        response = client.get("/api/v1/alerts/me/summary", headers=auth_headers(self.owner["id"]))

        self.assertEqual(response.status_code, 200, response.text)
        self.assertNotIn("diagnosis", response.text.lower())

    def test_family_alerts_allowed_and_denied(self) -> None:
        denied = client.get(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/alerts/active",
            headers=auth_headers(self.owner["id"]),
        )
        create_permission_for_member(self.family["id"], self.member["id"], share_all=True)
        personal = client.post("/api/v1/alerts/me", headers=auth_headers(self.member["id"]), json={**self._alert_payload(), "title": "Personal alert"})
        created = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/alerts",
            headers=auth_headers(self.owner["id"]),
            json=self._alert_payload(),
        )
        active = client.get(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/alerts/active",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(denied.status_code, 403)
        self.assertEqual(personal.status_code, 201, personal.text)
        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(len(active.json()["items"]), 1)
        self.assertEqual(active.json()["items"][0]["title"], "Document review")

    def _post_my_alert(self, *, due_at=None):
        payload = self._alert_payload()
        if due_at is not None:
            payload["due_at"] = due_at
        return client.post("/api/v1/alerts/me", headers=auth_headers(self.owner["id"]), json=payload)

    def _alert_payload(self):
        return {"alert_type": "document_review", "level": "attention", "title": "Document review", "message": "Review stored document metadata."}

    def _alert_event_count(self) -> int:
        with SessionLocal() as db:
            return len(list(db.scalars(select(AlertEvent.id))))


if __name__ == "__main__":
    unittest.main()
