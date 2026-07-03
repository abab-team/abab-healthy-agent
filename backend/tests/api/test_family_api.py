from __future__ import annotations

import unittest

from backend.tests.api.helpers import (
    add_member,
    auth_headers,
    client,
    create_family,
    create_user,
    reset_database,
)


class FamilyApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.owner = create_user("family_owner", nickname="Gala")
        self.father = create_user("family_father", nickname="Father")
        self.outsider = create_user("family_outsider", nickname="Outsider")
        created = create_family(self.owner["id"])
        self.family = created["family"]
        self.owner_member = created["owner_member"]

    def test_create_family_success(self) -> None:
        self.assertEqual(self.family["owner_user_id"], self.owner["id"])
        self.assertEqual(self.owner_member["user_id"], self.owner["id"])

    def test_list_my_families_returns_current_user_families(self) -> None:
        response = client.get("/api/v1/families", headers=auth_headers(self.owner["id"]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["id"], self.family["id"])

    def test_list_family_members(self) -> None:
        add_member(self.family["id"], self.owner["id"], self.father["id"], "爸爸", "爸爸")

        response = client.get(
            f"/api/v1/families/{self.family['id']}/members",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertNotIn("health_metrics", response.text)

    def test_add_registered_member_success(self) -> None:
        response = client.post(
            f"/api/v1/families/{self.family['id']}/members",
            headers=auth_headers(self.owner["id"]),
            json={
                "user_id": self.father["id"],
                "relationship_label": "爸爸",
                "display_name": "爸爸",
                "role": "member",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["user_id"], self.father["id"])

    def test_duplicate_member_returns_409(self) -> None:
        add_member(self.family["id"], self.owner["id"], self.father["id"], "爸爸", "爸爸")

        response = client.post(
            f"/api/v1/families/{self.family['id']}/members",
            headers=auth_headers(self.owner["id"]),
            json={
                "user_id": self.father["id"],
                "relationship_label": "爸爸",
                "display_name": "爸爸",
                "role": "member",
            },
        )

        self.assertEqual(response.status_code, 409)

    def test_current_user_outside_family_cannot_list_members(self) -> None:
        response = client.get(
            f"/api/v1/families/{self.family['id']}/members",
            headers=auth_headers(self.outsider["id"]),
        )

        self.assertEqual(response.status_code, 404)

    def test_resolve_self_reference(self) -> None:
        response = client.post(
            f"/api/v1/families/{self.family['id']}/resolve-member",
            headers=auth_headers(self.owner["id"]),
            json={"member_reference": "我"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["target_user_id"], self.owner["id"])

    def test_resolve_father_reference(self) -> None:
        add_member(self.family["id"], self.owner["id"], self.father["id"], "爸爸", "爸爸")

        response = client.post(
            f"/api/v1/families/{self.family['id']}/resolve-member",
            headers=auth_headers(self.owner["id"]),
            json={"member_reference": "爸爸"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["target_user_id"], self.father["id"])

    def test_resolve_unknown_reference_returns_error(self) -> None:
        response = client.post(
            f"/api/v1/families/{self.family['id']}/resolve-member",
            headers=auth_headers(self.owner["id"]),
            json={"member_reference": "不存在的成员"},
        )

        self.assertEqual(response.status_code, 404)

    def test_family_api_does_not_return_health_data(self) -> None:
        response = client.get(
            f"/api/v1/families/{self.family['id']}/members",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertNotIn("blood_pressure", response.text)
        self.assertNotIn("symptom_records", response.text)


if __name__ == "__main__":
    unittest.main()
