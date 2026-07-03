from __future__ import annotations

import unittest

from app.db.session import SessionLocal
from app.modules.family.exceptions import (
    FamilyMemberAlreadyExistsError,
    FamilyMemberNotFoundError,
    MemberReferenceNotFoundError,
)
from app.modules.family import service as family_service
from app.modules.identity import service as identity_service


class FamilyServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = SessionLocal()
        self.gala = identity_service.create_user(
            self.db,
            email="phase04a.family.gala@example.com",
            phone="phase04a_family_gala_phone",
            nickname="Gala",
        )
        self.father = identity_service.create_user(
            self.db,
            email="phase04a.family.father@example.com",
            phone="phase04a_family_father_phone",
            nickname="爸爸",
        )
        self.mother = identity_service.create_user(
            self.db,
            email="phase04a.family.mother@example.com",
            phone="phase04a_family_mother_phone",
            nickname="妈妈",
        )
        self.family = family_service.create_family_with_owner(
            self.db,
            owner_user_id=self.gala.id,
            family_name="Phase04A Family",
            owner_display_name="Gala",
        )

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()

    def test_create_family_with_owner_creates_owner_member(self) -> None:
        members = family_service.list_family_members(self.db, self.family.id)

        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].user_id, self.gala.id)
        self.assertEqual(members[0].relationship_label, "本人")

    def test_add_registered_member_and_prevent_duplicate(self) -> None:
        family_service.add_registered_member(
            self.db,
            family_id=self.family.id,
            user_id=self.father.id,
            relationship_label="爸爸",
            display_name="爸爸",
        )

        with self.assertRaises(FamilyMemberAlreadyExistsError):
            family_service.add_registered_member(
                self.db,
                family_id=self.family.id,
                user_id=self.father.id,
                relationship_label="爸爸",
                display_name="爸爸",
            )

    def test_list_family_members_returns_expected_members(self) -> None:
        family_service.add_registered_member(
            self.db,
            family_id=self.family.id,
            user_id=self.father.id,
            relationship_label="爸爸",
            display_name="爸爸",
        )
        family_service.add_registered_member(
            self.db,
            family_id=self.family.id,
            user_id=self.mother.id,
            relationship_label="妈妈",
            display_name="妈妈",
        )

        members = family_service.list_family_members(self.db, self.family.id)

        self.assertEqual(len(members), 3)

    def test_resolve_self_reference(self) -> None:
        result = family_service.resolve_member_reference(
            self.db,
            current_user_id=self.gala.id,
            current_family_id=self.family.id,
            member_reference="我",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.target_user_id, self.gala.id)

    def test_resolve_father_reference(self) -> None:
        family_service.add_registered_member(
            self.db,
            family_id=self.family.id,
            user_id=self.father.id,
            relationship_label="爸爸",
            display_name="爸爸",
        )

        result = family_service.resolve_member_reference(
            self.db,
            current_user_id=self.gala.id,
            current_family_id=self.family.id,
            member_reference="爸爸",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.target_user_id, self.father.id)

    def test_resolve_unknown_reference_does_not_guess(self) -> None:
        with self.assertRaises(MemberReferenceNotFoundError):
            family_service.resolve_member_reference(
                self.db,
                current_user_id=self.gala.id,
                current_family_id=self.family.id,
                member_reference="邻居",
            )

    def test_resolve_rejects_current_user_outside_family(self) -> None:
        outsider = identity_service.create_user(
            self.db,
            email="phase04a.family.outsider@example.com",
            phone="phase04a_family_outsider_phone",
            nickname="Outsider",
        )

        with self.assertRaises(FamilyMemberNotFoundError):
            family_service.resolve_member_reference(
                self.db,
                current_user_id=outsider.id,
                current_family_id=self.family.id,
                member_reference="爸爸",
            )


if __name__ == "__main__":
    unittest.main()
