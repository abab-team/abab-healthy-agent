from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ["JWT_SECRET_KEY"] = "api-test-jwt-secret"
BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from backend.tests.api.helpers import SessionLocal, client, reset_database  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.modules.auth.password import hash_password  # noqa: E402
from app.modules.identity.repository import create_user  # noqa: E402


class AuthApiTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["JWT_SECRET_KEY"] = "api-test-jwt-secret"
        get_settings.cache_clear()
        reset_database()
        with SessionLocal() as db:
            create_user(
                db,
                email="auth-api@example.com",
                nickname="Auth API",
                password_hash=hash_password("DemoPass123!"),
            )
            db.commit()

    def test_login_success_returns_tokens_and_user(self) -> None:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "auth-api@example.com", "password": "DemoPass123!"},
        )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["token_type"], "bearer")
        self.assertTrue(body["access_token"])
        self.assertTrue(body["refresh_token"])
        self.assertEqual(body["user"]["email"], "auth-api@example.com")

    def test_login_failure_does_not_return_token_or_password(self) -> None:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "auth-api@example.com", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 401, response.text)
        text = response.text.lower()
        self.assertNotIn("access_token", text)
        self.assertNotIn("refresh_token", text)
        self.assertNotIn("wrong-password", text)
        self.assertEqual(response.json()["detail"]["code"], "unauthorized")

    def test_refresh_logout_and_me_flow(self) -> None:
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "auth-api@example.com", "password": "DemoPass123!"},
        )
        self.assertEqual(login_response.status_code, 200, login_response.text)
        login_body = login_response.json()

        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {login_body['access_token']}"},
        )
        self.assertEqual(me_response.status_code, 200, me_response.text)
        self.assertEqual(me_response.json()["email"], "auth-api@example.com")

        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": login_body["refresh_token"]},
        )
        self.assertEqual(refresh_response.status_code, 200, refresh_response.text)
        refreshed_body = refresh_response.json()
        self.assertTrue(refreshed_body["access_token"])
        self.assertNotEqual(refreshed_body["refresh_token"], login_body["refresh_token"])

        old_refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": login_body["refresh_token"]},
        )
        self.assertEqual(old_refresh_response.status_code, 401, old_refresh_response.text)

        logout_response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refreshed_body["refresh_token"]},
        )
        self.assertEqual(logout_response.status_code, 200, logout_response.text)
        self.assertEqual(logout_response.json()["status"], "ok")

        after_logout_refresh = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refreshed_body["refresh_token"]},
        )
        self.assertEqual(after_logout_refresh.status_code, 401, after_logout_refresh.text)

    def test_auth_me_requires_bearer_token(self) -> None:
        response = client.get("/api/v1/auth/me")

        self.assertEqual(response.status_code, 401, response.text)
        self.assertEqual(response.json()["detail"]["code"], "unauthorized")


if __name__ == "__main__":
    unittest.main()
