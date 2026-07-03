from __future__ import annotations

import unittest

from backend.tests.api.helpers import auth_headers, client, create_user, reset_database


class IdentityApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()

    def test_create_user_success(self) -> None:
        response = client.post(
            "/api/v1/identity/users",
            json={"email": "identity.api@example.com", "nickname": "Identity API"},
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["email"], "identity.api@example.com")
        self.assertNotIn("password_hash", body)

    def test_duplicate_email_returns_409(self) -> None:
        payload = {"email": "identity.duplicate@example.com", "nickname": "First"}
        self.assertEqual(client.post("/api/v1/identity/users", json=payload).status_code, 201)

        response = client.post("/api/v1/identity/users", json=payload)

        self.assertEqual(response.status_code, 409)

    def test_me_requires_demo_header(self) -> None:
        response = client.get("/api/v1/identity/me")

        self.assertEqual(response.status_code, 401)
        self.assertIn("X-Current-User-Id", response.json()["detail"])

    def test_me_success_does_not_return_password_hash(self) -> None:
        user = create_user("identity_me", nickname="Current User")

        response = client.get("/api/v1/identity/me", headers=auth_headers(user["id"]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], user["id"])
        self.assertNotIn("password_hash", response.json())

    def test_update_me_profile_success(self) -> None:
        user = create_user("identity_profile", nickname="Before")

        response = client.patch(
            "/api/v1/identity/me/profile",
            headers=auth_headers(user["id"]),
            json={"nickname": "After", "avatar_url": "https://example.com/avatar.png"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["nickname"], "After")
        self.assertEqual(response.json()["avatar_url"], "https://example.com/avatar.png")

    def test_update_me_profile_rejects_account_security_fields(self) -> None:
        user = create_user("identity_forbidden", nickname="Before")

        response = client.patch(
            "/api/v1/identity/me/profile",
            headers=auth_headers(user["id"]),
            json={"password_hash": "nope", "status": "inactive", "email": "new@example.com", "phone": "123"},
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
