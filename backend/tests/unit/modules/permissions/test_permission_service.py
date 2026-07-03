from __future__ import annotations

import unittest

from app.db.session import SessionLocal
from app.modules.family import service as family_service
from app.modules.identity import service as identity_service
from app.modules.permissions import service as permission_service


class PermissionServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = SessionLocal()
        self.gala = identity_service.create_user(
            self.db,
            email="phase04a.permissions.gala@example.com",
            phone="p04a_perm_gala",
            nickname="Gala",
        )
        self.father = identity_service.create_user(
            self.db,
            email="phase04a.permissions.father@example.com",
            phone="p04a_perm_father",
            nickname="爸爸",
        )
        self.mother = identity_service.create_user(
            self.db,
            email="phase04a.permissions.mother@example.com",
            phone="p04a_perm_mother",
            nickname="妈妈",
        )
        self.family = family_service.create_family_with_owner(
            self.db,
            owner_user_id=self.gala.id,
            family_name="Phase04A Permission Family",
            owner_display_name="Gala",
        )
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
        for user in [self.gala, self.father, self.mother]:
            permission_service.create_default_permissions_for_member(
                self.db,
                family_id=self.family.id,
                user_id=user.id,
                share_all=True,
            )

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()

    def test_self_access_metrics_view_allowed(self) -> None:
        result = permission_service.check_member_permission(
            self.db,
            current_user_id=self.gala.id,
            family_id=None,
            target_user_id=self.gala.id,
            permission_type="metrics",
            action="view",
        )

        self.assertTrue(result.allowed)
        self.assertEqual(result.reason, "self_access")

    def test_family_share_all_allows_metrics_view(self) -> None:
        result = permission_service.check_member_permission(
            self.db,
            current_user_id=self.gala.id,
            family_id=self.family.id,
            target_user_id=self.father.id,
            permission_type="metrics",
            action="view",
        )

        self.assertTrue(result.allowed)
        self.assertEqual(result.reason, "family_share_all")

    def test_documents_view_can_be_denied_even_with_share_all(self) -> None:
        permission_service.update_share_permission(
            self.db,
            actor_user_id=self.father.id,
            family_id=self.family.id,
            target_user_id=self.father.id,
            updates={"can_view_documents": False},
            reason="test deny documents",
        )

        result = permission_service.check_member_permission(
            self.db,
            current_user_id=self.gala.id,
            family_id=self.family.id,
            target_user_id=self.father.id,
            permission_type="documents",
            action="view",
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "documents_not_shared")
        self.assertNotIn("体检报告", result.safe_message)

    def test_current_user_not_in_family_is_denied(self) -> None:
        outsider = identity_service.create_user(
            self.db,
            email="phase04a.permissions.outsider@example.com",
            phone="p04a_perm_out",
            nickname="Outsider",
        )

        result = permission_service.check_member_permission(
            self.db,
            current_user_id=outsider.id,
            family_id=self.family.id,
            target_user_id=self.father.id,
            permission_type="metrics",
            action="view",
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "current_user_not_in_family")

    def test_target_user_not_in_family_is_denied(self) -> None:
        outsider = identity_service.create_user(
            self.db,
            email="phase04a.permissions.target@example.com",
            phone="p04a_perm_target",
            nickname="Target",
        )

        result = permission_service.check_member_permission(
            self.db,
            current_user_id=self.gala.id,
            family_id=self.family.id,
            target_user_id=outsider.id,
            permission_type="metrics",
            action="view",
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "target_user_not_in_family")

    def test_share_all_false_uses_specific_field(self) -> None:
        permission_service.update_share_permission(
            self.db,
            actor_user_id=self.father.id,
            family_id=self.family.id,
            target_user_id=self.father.id,
            updates={"share_all": False, "can_view_metrics": True},
            reason="test metrics field",
        )

        allowed = permission_service.check_member_permission(
            self.db,
            current_user_id=self.gala.id,
            family_id=self.family.id,
            target_user_id=self.father.id,
            permission_type="metrics",
            action="view",
        )

        self.assertTrue(allowed.allowed)
        self.assertEqual(allowed.reason, "specific_permission_allowed")

    def test_export_and_generate_use_specific_fields(self) -> None:
        permission_service.update_share_permission(
            self.db,
            actor_user_id=self.father.id,
            family_id=self.family.id,
            target_user_id=self.father.id,
            updates={
                "share_all": False,
                "can_export_summary": False,
                "can_generate_doctor_visit_summary": True,
            },
            reason="test export generate fields",
        )

        export_result = permission_service.check_member_permission(
            self.db,
            current_user_id=self.gala.id,
            family_id=self.family.id,
            target_user_id=self.father.id,
            permission_type="reports",
            action="export",
        )
        generate_result = permission_service.check_member_permission(
            self.db,
            current_user_id=self.gala.id,
            family_id=self.family.id,
            target_user_id=self.father.id,
            permission_type="doctor_visit_summary",
            action="generate",
        )

        self.assertFalse(export_result.allowed)
        self.assertEqual(export_result.reason, "export_not_allowed")
        self.assertTrue(generate_result.allowed)


if __name__ == "__main__":
    unittest.main()
