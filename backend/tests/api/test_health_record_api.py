from __future__ import annotations

import unittest

from tests.api.helpers import (
    add_member,
    auth_headers,
    client,
    create_family,
    create_permission_for_member,
    create_user,
    reset_database,
)


class HealthRecordApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.owner = create_user("record_owner")
        self.member = create_user("record_member")
        self.outsider = create_user("record_outsider")
        self.family = create_family(self.owner["id"])["family"]
        add_member(
            self.family["id"],
            self.owner["id"],
            self.member["id"],
            "parent",
            "Parent",
        )

    def test_create_my_symptom(self) -> None:
        response = self._post_my_symptom()

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["symptom_name"], "headache")

    def test_get_my_recent_symptoms(self) -> None:
        self._post_my_symptom()

        response = client.get(
            "/api/v1/health-records/me/symptoms/recent",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()["items"]), 1)

    def test_get_my_symptom_summary(self) -> None:
        self._post_my_symptom()

        response = client.get(
            "/api/v1/health-records/me/symptoms/summary",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["count"], 1)

    def test_create_my_draft(self) -> None:
        response = self._post_my_draft()

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["status"], "pending")

    def test_get_my_pending_drafts(self) -> None:
        self._post_my_draft()

        response = client.get(
            "/api/v1/health-records/me/drafts/pending",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()["items"]), 1)

    def test_confirm_my_draft_creates_symptom(self) -> None:
        draft_id = self._post_my_draft().json()["id"]

        response = client.post(
            f"/api/v1/health-records/me/drafts/{draft_id}/confirm",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["symptom_name"], "cough")

    def test_confirm_my_draft_twice_conflicts(self) -> None:
        draft_id = self._post_my_draft().json()["id"]
        client.post(
            f"/api/v1/health-records/me/drafts/{draft_id}/confirm",
            headers=auth_headers(self.owner["id"]),
        )

        response = client.post(
            f"/api/v1/health-records/me/drafts/{draft_id}/confirm",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 409)

    def test_cancel_my_pending_draft(self) -> None:
        draft_id = self._post_my_draft().json()["id"]

        response = client.post(
            f"/api/v1/health-records/me/drafts/{draft_id}/cancel",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "cancelled")

    def test_cancel_non_pending_draft_conflicts(self) -> None:
        draft_id = self._post_my_draft().json()["id"]
        client.post(
            f"/api/v1/health-records/me/drafts/{draft_id}/confirm",
            headers=auth_headers(self.owner["id"]),
        )

        response = client.post(
            f"/api/v1/health-records/me/drafts/{draft_id}/cancel",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 409)

    def test_family_create_symptom_allowed(self) -> None:
        create_permission_for_member(self.family["id"], self.member["id"], share_all=True)

        response = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/health-records/symptoms",
            headers=auth_headers(self.owner["id"]),
            json={"raw_text": "cough", "symptom_name": "cough"},
        )

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["user_id"], self.member["id"])

    def test_family_recent_symptoms_denied_without_permission(self) -> None:
        response = client.get(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/health-records/symptoms/recent",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 403)

    def test_family_recent_symptoms_are_limited_to_family_scope(self) -> None:
        create_permission_for_member(self.family["id"], self.member["id"], share_all=True)
        client.post(
            "/api/v1/health-records/me/symptoms",
            headers=auth_headers(self.member["id"]),
            json={"raw_text": "personal cough", "symptom_name": "personal"},
        )
        client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/health-records/symptoms",
            headers=auth_headers(self.owner["id"]),
            json={"raw_text": "family cough", "symptom_name": "family"},
        )

        response = client.get(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/health-records/symptoms/recent",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 200, response.text)
        items = response.json()["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["symptom_name"], "family")

    def test_my_pending_drafts_are_limited_to_personal_scope(self) -> None:
        create_permission_for_member(self.family["id"], self.member["id"], share_all=True)
        self._post_family_draft()

        response = client.get(
            "/api/v1/health-records/me/drafts/pending",
            headers=auth_headers(self.member["id"]),
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["items"], [])

    def test_family_create_draft_allowed(self) -> None:
        create_permission_for_member(self.family["id"], self.member["id"], share_all=True)

        response = self._post_family_draft()

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["user_id"], self.member["id"])

    def test_family_confirm_draft_with_wrong_target_is_hidden(self) -> None:
        create_permission_for_member(self.family["id"], self.member["id"], share_all=True)
        create_permission_for_member(self.family["id"], self.owner["id"], share_all=True)
        draft_id = self._post_family_draft().json()["id"]

        response = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.owner['id']}/health-records/drafts/{draft_id}/confirm",
            headers=auth_headers(self.member["id"]),
        )

        self.assertEqual(response.status_code, 404)

    def test_family_cancel_draft_denied_without_permission(self) -> None:
        create_permission_for_member(self.family["id"], self.member["id"], share_all=True)
        draft_id = self._post_family_draft().json()["id"]

        response = client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/health-records/drafts/{draft_id}/cancel",
            headers=auth_headers(self.outsider["id"]),
        )

        self.assertEqual(response.status_code, 403)

    def _post_my_symptom(self):
        return client.post(
            "/api/v1/health-records/me/symptoms",
            headers=auth_headers(self.owner["id"]),
            json={"raw_text": "headache", "symptom_name": "headache"},
        )

    def _post_my_draft(self):
        return client.post(
            "/api/v1/health-records/me/drafts",
            headers=auth_headers(self.owner["id"]),
            json={
                "raw_text": "cough",
                "draft_type": "symptom",
                "extracted_json": {"symptom_name": "cough"},
            },
        )

    def _post_family_draft(self):
        return client.post(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/health-records/drafts",
            headers=auth_headers(self.owner["id"]),
            json={
                "raw_text": "cough",
                "draft_type": "symptom",
                "extracted_json": {"symptom_name": "cough"},
            },
        )


if __name__ == "__main__":
    unittest.main()
