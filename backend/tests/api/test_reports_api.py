from __future__ import annotations

import unittest
from datetime import date, timedelta

from tests.api.helpers import (
    add_member,
    auth_headers,
    client,
    create_family,
    create_permission_for_member,
    create_user,
    reset_database,
)


class ReportsApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.owner = create_user("report_owner")
        self.member = create_user("report_member")
        self.family = create_family(self.owner["id"])["family"]
        add_member(self.family["id"], self.owner["id"], self.member["id"], "parent", "Parent")

    def test_save_upsert_latest_recent_and_mark_failed(self) -> None:
        today = date.today().isoformat()
        first = self._save_my_report(today, "first")
        second = self._save_my_report(today, "second")
        latest = client.get("/api/v1/reports/me/daily/latest", headers=auth_headers(self.owner["id"]))
        recent = client.get("/api/v1/reports/me/daily/recent", headers=auth_headers(self.owner["id"]))
        failed = client.post(f"/api/v1/reports/me/daily/{today}/mark-failed", headers=auth_headers(self.owner["id"]))

        self.assertEqual(first.status_code, 201, first.text)
        self.assertEqual(first.json()["id"], second.json()["id"])
        self.assertEqual(latest.json()["summary_text"], "second")
        self.assertEqual(len(recent.json()["items"]), 1)
        self.assertEqual(failed.json()["generation_status"], "failed")

    def test_no_report_snapshot_does_not_claim_health_ok(self) -> None:
        response = client.get("/api/v1/reports/me/daily/latest", headers=auth_headers(self.owner["id"]))

        self.assertEqual(response.status_code, 200, response.text)
        self.assertFalse(response.json()["has_report"])
        self.assertNotIn("healthy", response.json()["message"].lower())

    def test_family_reports_permissions(self) -> None:
        family_date = (date.today() - timedelta(days=1)).isoformat()
        personal = client.post(
            "/api/v1/reports/me/daily",
            headers=auth_headers(self.member["id"]),
            json=self._report_payload(date.today().isoformat(), "member personal"),
        )
        denied = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/reports/daily",
            headers=auth_headers(self.owner["id"]),
            json=self._report_payload(family_date, "denied"),
        )
        create_permission_for_member(self.family["id"], self.member["id"], share_all=True)
        created = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/reports/daily",
            headers=auth_headers(self.owner["id"]),
            json=self._report_payload(family_date, "family"),
        )
        latest = client.get(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/reports/daily/latest",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(personal.status_code, 201, personal.text)
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(latest.json()["summary_text"], "family")

    def _save_my_report(self, report_date, summary):
        return client.post("/api/v1/reports/me/daily", headers=auth_headers(self.owner["id"]), json=self._report_payload(report_date, summary))

    def _report_payload(self, report_date, summary):
        return {"report_date": report_date, "status_level": "insufficient_data", "summary_text": summary}


if __name__ == "__main__":
    unittest.main()
