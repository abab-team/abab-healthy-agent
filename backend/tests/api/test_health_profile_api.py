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


class HealthProfileApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.owner = create_user("profile_owner")
        self.member = create_user("profile_member")
        self.family = create_family(self.owner["id"])["family"]
        add_member(
            self.family["id"],
            self.owner["id"],
            self.member["id"],
            "parent",
            "Parent",
        )

    def test_get_my_health_profile_creates_snapshot(self) -> None:
        response = client.get(
            "/api/v1/health-profile/me",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["user_id"], self.owner["id"])

    def test_patch_my_health_profile_updates_allowed_fields(self) -> None:
        response = client.patch(
            "/api/v1/health-profile/me",
            headers=auth_headers(self.owner["id"]),
            json={"height_cm": 172.5, "gender": "unknown", "blood_type": "O"},
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["height_cm"], 172.5)
        self.assertEqual(response.json()["blood_type"], "O")

    def test_missing_demo_header_is_rejected(self) -> None:
        response = client.get("/api/v1/health-profile/me")

        self.assertEqual(response.status_code, 401)

    def test_get_family_member_profile_when_permission_allows(self) -> None:
        create_permission_for_member(self.family["id"], self.member["id"], share_all=True)

        response = client.get(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/health-profile",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["user_id"], self.member["id"])

    def test_get_family_member_profile_denied_without_permission(self) -> None:
        response = client.get(
            f"/api/v1/families/{self.family['id']}/members/{self.member['id']}/health-profile",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
