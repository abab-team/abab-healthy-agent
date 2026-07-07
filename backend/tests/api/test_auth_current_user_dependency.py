from __future__ import annotations

import unittest
import sys
from pathlib import Path
from uuid import UUID

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from backend.tests.api.helpers import auth_headers, client, create_family, create_user, reset_database

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal
from app.modules.auth import service as auth_service
from app.modules.auth.password import hash_password
from app.modules.identity.models import User
from app.modules.identity.enums import UserStatus


class AuthCurrentUserDependencyTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        client.app.dependency_overrides.pop(get_settings, None)

    def tearDown(self) -> None:
        client.app.dependency_overrides.pop(get_settings, None)

    def test_demo_header_disabled_without_jwt_returns_401(self) -> None:
        user = create_user("auth_dep_demo_disabled", nickname="Demo Disabled")
        client.app.dependency_overrides[get_settings] = lambda: self._settings(demo_header_enabled=False)

        response = client.get("/api/v1/identity/me", headers=auth_headers(user["id"]))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"]["code"], "missing_current_user")

    def test_jwt_can_access_identity_me_when_demo_header_disabled(self) -> None:
        user = self._create_password_user("jwt_identity@example.com", "JWT Identity")
        token_pair = self._login("jwt_identity@example.com")
        client.app.dependency_overrides[get_settings] = lambda: self._settings(demo_header_enabled=False)

        response = client.get("/api/v1/identity/me", headers=self._bearer_headers(token_pair.access_token))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], str(user.id))
        self.assertNotIn("access_token", response.text)
        self.assertNotIn("refresh_token", response.text)

    def test_bearer_token_takes_precedence_over_demo_header(self) -> None:
        jwt_user = self._create_password_user("jwt_precedence@example.com", "JWT User")
        header_user = create_user("auth_dep_header_user", nickname="Header User")
        token_pair = self._login("jwt_precedence@example.com")

        response = client.get(
            "/api/v1/identity/me",
            headers={**auth_headers(header_user["id"]), **self._bearer_headers(token_pair.access_token)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], str(jwt_user.id))

    def test_invalid_bearer_token_does_not_fallback_to_demo_header(self) -> None:
        header_user = create_user("auth_dep_invalid_token_header", nickname="Header User")

        response = client.get(
            "/api/v1/identity/me",
            headers={**auth_headers(header_user["id"]), "Authorization": "Bearer invalid.token.value"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"]["code"], "unauthorized")

    def test_agent_api_uses_jwt_current_user(self) -> None:
        user = self._create_password_user("jwt_agent@example.com", "JWT Agent")
        token_pair = self._login("jwt_agent@example.com")
        client.app.dependency_overrides[get_settings] = lambda: self._settings(demo_header_enabled=False)

        response = client.post(
            "/api/v1/agent/runs",
            headers=self._bearer_headers(token_pair.access_token),
            json={
                "target_user_id": str(user.id),
                "workflow_type": "daily_health_brief",
                "user_message": "Please summarize my system records.",
                "source": "jwt_api_test",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["workflow_type"], "daily_health_brief")
        self.assertEqual(response.json()["status"], "completed")

    def test_jwt_user_without_family_permission_is_denied(self) -> None:
        actor = self._create_password_user("jwt_family_actor@example.com", "JWT Actor")
        target = create_user("jwt_family_target", nickname="Target")
        other = create_user("jwt_family_other", nickname="Other")
        family = create_family(other["id"])["family"]
        token_pair = self._login("jwt_family_actor@example.com")
        client.app.dependency_overrides[get_settings] = lambda: self._settings(demo_header_enabled=False)

        response = client.get(
            f"/api/v1/families/{family['id']}/members/{target['id']}/health-profile",
            headers=self._bearer_headers(token_pair.access_token),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"]["code"], "permission_denied")
        self.assertNotIn(target["email"], response.text)

    def _create_password_user(self, email: str, nickname: str) -> User:
        with SessionLocal() as db:
            user = User(
                email=email,
                password_hash=hash_password("DemoPass123!"),
                nickname=nickname,
                status=UserStatus.ACTIVE,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            user_id = user.id
        with SessionLocal() as db:
            loaded = db.get(User, UUID(str(user_id)))
            assert loaded is not None
            return loaded

    def _login(self, email: str):
        with SessionLocal() as db:
            token_pair = auth_service.login_with_password(
                db,
                self._settings(),
                email=email,
                password="DemoPass123!",
            )
            db.commit()
            return token_pair

    def _settings(self, *, demo_header_enabled: bool = True) -> Settings:
        return Settings(
            JWT_SECRET_KEY="api-test-jwt-secret",
            AUTH_DEMO_HEADER_ENABLED=demo_header_enabled,
            AUTH_DEMO_LOGIN_ENABLED=True,
            AUTH_ENABLED=False,
        )

    def _bearer_headers(self, access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}"}


if __name__ == "__main__":
    unittest.main()
