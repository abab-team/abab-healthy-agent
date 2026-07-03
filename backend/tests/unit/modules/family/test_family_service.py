# 模块领域：家庭成员模块
# 领域说明：负责家庭、成员关系、邀请流程和自然语言成员称呼解析。
# 文件职责：测试文件。固定模块关键行为，帮助持续迭代时发现回归。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

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


# 类职责：FamilyServiceTestCase 承载 家庭成员模块 中的一组相关状态或行为。
# 设计边界：保持职责集中，避免把跨模块编排逻辑塞进单个类型。继承/混入：TestCase。
class FamilyServiceTestCase(unittest.TestCase):
    # 函数职责：业务函数，封装 家庭成员模块 中的一段可复用逻辑。
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

    # 函数职责：业务函数，封装 家庭成员模块 中的一段可复用逻辑。
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
    def test_create_family_with_owner_creates_owner_member(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        members = family_service.list_family_members(self.db, self.family.id)

        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].user_id, self.gala.id)
        self.assertEqual(members[0].relationship_label, "本人")

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_add_registered_member_and_prevent_duplicate(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        family_service.add_registered_member(
            self.db,
            family_id=self.family.id,
            user_id=self.father.id,
            relationship_label="爸爸",
            display_name="爸爸",
        )

        # 上下文说明：在受控资源边界内执行，确保会话、文件或事务被正确释放。
        with self.assertRaises(FamilyMemberAlreadyExistsError):
            family_service.add_registered_member(
                self.db,
                family_id=self.family.id,
                user_id=self.father.id,
                relationship_label="爸爸",
                display_name="爸爸",
            )

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_list_family_members_returns_expected_members(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
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

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_resolve_self_reference(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        result = family_service.resolve_member_reference(
            self.db,
            current_user_id=self.gala.id,
            current_family_id=self.family.id,
            member_reference="我",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.target_user_id, self.gala.id)

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_resolve_father_reference(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
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

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_resolve_unknown_reference_does_not_guess(self) -> None:
        # 上下文说明：在受控资源边界内执行，确保会话、文件或事务被正确释放。
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        with self.assertRaises(MemberReferenceNotFoundError):
            family_service.resolve_member_reference(
                self.db,
                current_user_id=self.gala.id,
                current_family_id=self.family.id,
                member_reference="邻居",
            )

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_resolve_rejects_current_user_outside_family(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        outsider = identity_service.create_user(
            self.db,
            email="phase04a.family.outsider@example.com",
            phone="phase04a_family_outsider_phone",
            nickname="Outsider",
        )

        # 上下文说明：在受控资源边界内执行，确保会话、文件或事务被正确释放。
        with self.assertRaises(FamilyMemberNotFoundError):
            family_service.resolve_member_reference(
                self.db,
                current_user_id=outsider.id,
                current_family_id=self.family.id,
                member_reference="爸爸",
            )


# 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
if __name__ == "__main__":
    unittest.main()
