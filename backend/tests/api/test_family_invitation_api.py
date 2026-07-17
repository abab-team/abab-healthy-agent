from __future__ import annotations

import unittest

from backend.tests.api.helpers import auth_headers, client, create_user, reset_database


class FamilyInvitationApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.owner = create_user("family_owner", nickname="Owner")
        self.joiner = create_user("family_joiner", nickname="Joiner")
        self.outsider = create_user("family_outsider", nickname="Outsider")

    def test_create_and_join_by_single_use_code_starts_private(self) -> None:
        created = client.post(
            "/api/v1/families",
            headers=auth_headers(self.owner["id"]),
            json={"name": "Private Family", "owner_display_name": "Owner"},
        )
        self.assertEqual(created.status_code, 201, created.text)
        body = created.json()
        family_id = body["family"]["id"]
        code = body["invitation"]["invite_code"]
        self.assertEqual(len(code), 8)

        owner_permission = client.get(
            f"/api/v1/families/{family_id}/members/{self.owner['id']}/permissions",
            headers=auth_headers(self.owner["id"]),
        )
        self.assertFalse(owner_permission.json()["share_all"])

        joined = client.post("/api/v1/families/join-by-code", headers=auth_headers(self.joiner["id"]), json={"invite_code": code})
        self.assertEqual(joined.status_code, 201, joined.text)
        self.assertEqual(joined.json()["family"]["id"], family_id)

        joiner_permission = client.get(
            f"/api/v1/families/{family_id}/members/{self.joiner['id']}/permissions",
            headers=auth_headers(self.joiner["id"]),
        )
        self.assertFalse(joiner_permission.json()["share_all"])
        self.assertEqual(
            client.post("/api/v1/families/join-by-code", headers=auth_headers(self.outsider["id"]), json={"invite_code": code}).status_code,
            400,
        )

    def test_member_can_only_change_own_sharing_settings(self) -> None:
        created = client.post("/api/v1/families", headers=auth_headers(self.owner["id"]), json={"name": "Private Family"}).json()
        family_id = created["family"]["id"]
        client.post("/api/v1/families/join-by-code", headers=auth_headers(self.joiner["id"]), json={"invite_code": created["invitation"]["invite_code"]})

        denied = client.patch(
            f"/api/v1/families/{family_id}/members/{self.joiner['id']}/permissions",
            headers=auth_headers(self.owner["id"]),
            json={"can_view_metrics": True},
        )
        self.assertEqual(denied.status_code, 403)
        allowed = client.patch(
            f"/api/v1/families/{family_id}/members/{self.joiner['id']}/permissions",
            headers=auth_headers(self.joiner["id"]),
            json={"can_view_metrics": True},
        )
        self.assertEqual(allowed.status_code, 200)
        self.assertTrue(allowed.json()["can_view_metrics"])


if __name__ == "__main__":
    unittest.main()
