from __future__ import annotations

import unittest
from datetime import date

from tests.api.helpers import (
    add_member,
    auth_headers,
    client,
    create_family,
    create_permission_for_member,
    create_user,
    reset_database,
)


class MedicalTimelineApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.owner = create_user("medical_owner")
        self.member = create_user("medical_member")
        self.family = create_family(self.owner["id"])["family"]
        add_member(self.family["id"], self.owner["id"], self.member["id"], "parent", "Parent")

    def test_create_my_event_and_does_not_generate_diagnosis(self) -> None:
        response = self._post_my_event({"title": "Checkup", "event_type": "checkup", "follow_up_needed": True})

        self.assertEqual(response.status_code, 201, response.text)
        self.assertIsNone(response.json()["diagnosis_text"])

    def test_get_events_summary_followups_and_archive(self) -> None:
        event = self._post_my_event(
            {
                "title": "Follow",
                "event_type": "follow_up",
                "event_date": date.today().isoformat(),
                "follow_up_needed": True,
            }
        ).json()

        events = client.get("/api/v1/medical-timeline/me/events", headers=auth_headers(self.owner["id"]))
        summary = client.get("/api/v1/medical-timeline/me/events/summary", headers=auth_headers(self.owner["id"]))
        followups = client.get("/api/v1/medical-timeline/me/events/follow-ups", headers=auth_headers(self.owner["id"]))
        archived = client.post(f"/api/v1/medical-timeline/me/events/{event['id']}/archive", headers=auth_headers(self.owner["id"]))

        self.assertEqual(events.status_code, 200, events.text)
        self.assertEqual(summary.json()["count"], 1)
        self.assertEqual(len(followups.json()["items"]), 1)
        self.assertEqual(archived.json()["status"], "archived")

    def test_family_view_and_create_permissions(self) -> None:
        create_permission_for_member(self.family["id"], self.member["id"], share_all=True)

        created = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/medical-timeline/events",
            headers=auth_headers(self.owner["id"]),
            json={"title": "Family checkup", "event_type": "checkup", "event_date": date.today().isoformat()},
        )
        listed = client.get(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/medical-timeline/events",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(len(listed.json()["items"]), 1)

    def test_family_permissions_denied_before_data_access(self) -> None:
        denied_create = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/medical-timeline/events",
            headers=auth_headers(self.owner["id"]),
            json={"title": "Denied", "event_type": "checkup"},
        )
        denied_view = client.get(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/medical-timeline/events",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(denied_create.status_code, 403)
        self.assertEqual(denied_view.status_code, 403)

    def _post_my_event(self, payload):
        return client.post("/api/v1/medical-timeline/me/events", headers=auth_headers(self.owner["id"]), json=payload)


if __name__ == "__main__":
    unittest.main()
