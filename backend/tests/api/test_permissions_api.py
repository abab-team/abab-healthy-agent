from __future__ import annotations

import unittest

from backend.tests.api.helpers import (
    add_member,
    auth_headers,
    client,
    count_permission_audit_logs,
    create_family,
    create_permission_for_member,
    create_user,
    reset_database,
)


class PermissionsApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.owner = create_user("perm_owner", nickname="Gala")
        self.father = create_user("perm_father", nickname="Father")
        self.outsider = create_user("perm_outsider", nickname="Outsider")
        self.family = create_family(self.owner["id"])["family"]
        add_member(self.family["id"], self.owner["id"], self.father["id"], "爸爸", "爸爸")
        create_permission_for_member(self.family["id"], self.owner["id"], share_all=True)
        create_permission_for_member(self.family["id"], self.father["id"], share_all=True)

    def test_list_family_permissions_success(self) -> None:
        response = client.get(
            f"/api/v1/families/{self.family['id']}/permissions",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json()), 2)
        self.assertNotIn("health_metrics", response.text)

    def test_get_single_member_permissions_success(self) -> None:
        response = client.get(
            f"/api/v1/families/{self.family['id']}/members/{self.father['id']}/permissions",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user_id"], self.father["id"])

    def test_patch_permissions_updates_documents_and_records_audit(self) -> None:
        before = count_permission_audit_logs()

        response = client.patch(
            f"/api/v1/families/{self.family['id']}/members/{self.father['id']}/permissions",
            headers=auth_headers(self.owner["id"]),
            json={"can_view_documents": False, "reason": "API test"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["can_view_documents"])
        self.assertEqual(count_permission_audit_logs(), before + 1)

    def test_permission_check_metrics_view_allowed_with_share_all(self) -> None:
        response = client.post(
            f"/api/v1/families/{self.family['id']}/permissions/check",
            headers=auth_headers(self.owner["id"]),
            json={"target_user_id": self.father["id"], "permission_type": "metrics", "action": "view"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["allowed"])

    def test_permission_check_documents_denied_when_specific_field_false(self) -> None:
        client.patch(
            f"/api/v1/families/{self.family['id']}/members/{self.father['id']}/permissions",
            headers=auth_headers(self.owner["id"]),
            json={"can_view_documents": False, "reason": "API test"},
        )

        response = client.post(
            f"/api/v1/families/{self.family['id']}/permissions/check",
            headers=auth_headers(self.owner["id"]),
            json={"target_user_id": self.father["id"], "permission_type": "documents", "action": "view"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["allowed"])
        self.assertNotIn("体检报告", response.json()["safe_message"])

    def test_denied_safe_message_does_not_reveal_data_existence(self) -> None:
        response = client.post(
            f"/api/v1/families/{self.family['id']}/permissions/check",
            headers=auth_headers(self.owner["id"]),
            json={"target_user_id": self.father["id"], "permission_type": "unknown", "action": "view"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["allowed"])
        self.assertNotIn("存在", response.json()["safe_message"])

    def test_current_user_outside_family_is_denied(self) -> None:
        response = client.post(
            f"/api/v1/families/{self.family['id']}/permissions/check",
            headers=auth_headers(self.outsider["id"]),
            json={"target_user_id": self.father["id"], "permission_type": "metrics", "action": "view"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["allowed"])

    def test_permission_api_does_not_return_health_data(self) -> None:
        response = client.get(
            f"/api/v1/families/{self.family['id']}/permissions",
            headers=auth_headers(self.owner["id"]),
        )

        self.assertNotIn("blood_pressure", response.text)
        self.assertNotIn("systolic", response.text)
        self.assertNotIn("diastolic", response.text)


if __name__ == "__main__":
    unittest.main()
