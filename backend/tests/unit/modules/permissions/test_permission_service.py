# 模块领域：权限模块
# 领域说明：负责家庭成员之间的数据共享范围、访问策略和越权拦截。
# 文件职责：测试文件。固定模块关键行为，帮助持续迭代时发现回归。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

import unittest

from app.db.session import SessionLocal
from app.modules.family import service as family_service
from app.modules.identity import service as identity_service
from app.modules.permissions import service as permission_service


# 类职责：PermissionServiceTestCase 承载 权限模块 中的一组相关状态或行为。
# 设计边界：保持职责集中，避免把跨模块编排逻辑塞进单个类型。继承/混入：TestCase。
class PermissionServiceTestCase(unittest.TestCase):
    # 函数职责：业务函数，封装 权限模块 中的一段可复用逻辑。
    # 业务边界：调用方应根据返回值和异常语义处理成功与失败。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    def setUp(self) -> None:
        # 流程说明：
        # 1. 接收上游传入的数据或上下文。
        # 2. 完成本函数职责范围内的处理。
        # 3. 将结果返回给调用方，继续由上层流程编排。
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
        # 循环说明：逐项处理集合中的业务对象，保持每个元素处理逻辑一致。
        for user in [self.gala, self.father, self.mother]:
            permission_service.create_default_permissions_for_member(
                self.db,
                family_id=self.family.id,
                user_id=user.id,
                share_all=True,
            )

    # 函数职责：业务函数，封装 权限模块 中的一段可复用逻辑。
    # 业务边界：调用方应根据返回值和异常语义处理成功与失败。
    def tearDown(self) -> None:
        # 流程说明：
        # 1. 接收上游传入的数据或上下文。
        # 2. 完成本函数职责范围内的处理。
        # 3. 将结果返回给调用方，继续由上层流程编排。
        self.db.rollback()
        self.db.close()

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_self_access_metrics_view_allowed(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
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

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_family_share_all_allows_metrics_view(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
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

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_documents_view_can_be_denied_even_with_share_all(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
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

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_current_user_not_in_family_is_denied(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
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

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_target_user_not_in_family_is_denied(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
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

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_share_all_false_uses_specific_field(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
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

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_export_and_generate_use_specific_fields(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
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


# 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
if __name__ == "__main__":
    unittest.main()
