from __future__ import annotations

import os
import unittest

from sqlalchemy import delete

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ["JWT_SECRET_KEY"] = "unit-test-jwt-secret"

from app.core.config import Settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.modules.auth import service  # noqa: E402
from app.modules.auth.exceptions import InvalidCredentialsError, InvalidTokenError  # noqa: E402
from app.modules.auth.password import hash_password, verify_password  # noqa: E402
from app.modules.identity.models import LoginSession, RefreshToken, User  # noqa: E402
from app.modules.identity.repository import create_user  # noqa: E402


class AuthServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        engine.dispose()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            db.execute(delete(LoginSession))
            db.execute(delete(RefreshToken))
            db.execute(delete(User))
            db.commit()
        self.settings = Settings(
            JWT_SECRET_KEY="unit-test-jwt-secret",
            ACCESS_TOKEN_EXPIRE_MINUTES=15,
            REFRESH_TOKEN_EXPIRE_DAYS=30,
        )

    def test_password_hash_and_verify(self) -> None:
        password_hash = hash_password("DemoPass123!")

        self.assertNotEqual(password_hash, "DemoPass123!")
        self.assertTrue(verify_password("DemoPass123!", password_hash))
        self.assertFalse(verify_password("wrong-password", password_hash))

    def test_login_returns_access_and_refresh_tokens(self) -> None:
        with SessionLocal() as db:
            create_user(
                db,
                email="auth-user@example.com",
                nickname="Auth User",
                password_hash=hash_password("DemoPass123!"),
            )
            token_pair = service.login_with_password(
                db,
                self.settings,
                email="auth-user@example.com",
                password="DemoPass123!",
            )

            self.assertEqual(token_pair.token_type, "bearer")
            self.assertTrue(token_pair.access_token)
            self.assertTrue(token_pair.refresh_token)
            self.assertNotIn("DemoPass123!", token_pair.access_token)
            self.assertNotIn("DemoPass123!", token_pair.refresh_token)

    def test_login_failure_returns_no_token(self) -> None:
        with SessionLocal() as db:
            create_user(
                db,
                email="auth-user@example.com",
                password_hash=hash_password("DemoPass123!"),
            )

            with self.assertRaises(InvalidCredentialsError):
                service.login_with_password(
                    db,
                    self.settings,
                    email="auth-user@example.com",
                    password="wrong-password",
                )

    def test_refresh_rotates_token_and_logout_revokes_refresh_token(self) -> None:
        with SessionLocal() as db:
            create_user(
                db,
                email="auth-user@example.com",
                password_hash=hash_password("DemoPass123!"),
            )
            first_pair = service.login_with_password(
                db,
                self.settings,
                email="auth-user@example.com",
                password="DemoPass123!",
            )
            second_pair = service.refresh_access_token(db, self.settings, refresh_token=first_pair.refresh_token)

            self.assertTrue(second_pair.access_token)
            self.assertNotEqual(first_pair.refresh_token, second_pair.refresh_token)
            with self.assertRaises(InvalidTokenError):
                service.refresh_access_token(db, self.settings, refresh_token=first_pair.refresh_token)

            service.logout(db, refresh_token=second_pair.refresh_token)
            with self.assertRaises(InvalidTokenError):
                service.refresh_access_token(db, self.settings, refresh_token=second_pair.refresh_token)

    def test_authenticate_access_token_returns_current_user(self) -> None:
        with SessionLocal() as db:
            create_user(
                db,
                email="auth-user@example.com",
                nickname="Auth User",
                password_hash=hash_password("DemoPass123!"),
            )
            token_pair = service.login_with_password(
                db,
                self.settings,
                email="auth-user@example.com",
                password="DemoPass123!",
            )
            auth_user = service.authenticate_access_token(db, self.settings, token_pair.access_token)

            self.assertEqual(auth_user.user.email, "auth-user@example.com")
            self.assertTrue(auth_user.session_id)


if __name__ == "__main__":
    unittest.main()
