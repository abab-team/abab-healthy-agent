from __future__ import annotations

import unittest
from datetime import date

from app.db.session import SessionLocal
from app.modules.identity.enums import Gender
from app.modules.identity.exceptions import UserAlreadyExistsError
from app.modules.identity import service as identity_service


class IdentityServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = SessionLocal()

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()

    def test_create_user_success_does_not_expose_password_hash(self) -> None:
        user = identity_service.create_user(
            self.db,
            email="phase04a.identity@example.com",
            phone="phase04a_identity_phone",
            nickname="Phase04A Identity",
            password_hash="demo_hash_not_plain_token",
            gender=Gender.UNKNOWN,
            birth_date=date(2000, 1, 1),
        )

        self.assertEqual(user.email, "phase04a.identity@example.com")
        self.assertFalse(hasattr(user, "password_hash"))

    def test_duplicate_email_is_rejected(self) -> None:
        identity_service.create_user(
            self.db,
            email="phase04a.duplicate@example.com",
            nickname="First",
        )

        with self.assertRaises(UserAlreadyExistsError):
            identity_service.create_user(
                self.db,
                email="phase04a.duplicate@example.com",
                nickname="Second",
            )

    def test_get_user_by_email_and_phone(self) -> None:
        created = identity_service.create_user(
            self.db,
            email="phase04a.lookup@example.com",
            phone="phase04a_lookup_phone",
            nickname="Lookup",
        )

        by_email = identity_service.get_user_by_email(
            self.db,
            "phase04a.lookup@example.com",
        )
        by_phone = identity_service.get_user_by_phone(
            self.db,
            "phase04a_lookup_phone",
        )

        self.assertIsNotNone(by_email)
        self.assertIsNotNone(by_phone)
        self.assertEqual(by_email.id, created.id)
        self.assertEqual(by_phone.id, created.id)


if __name__ == "__main__":
    unittest.main()
