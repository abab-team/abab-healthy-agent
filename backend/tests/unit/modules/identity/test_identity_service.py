# 模块领域：用户身份模块
# 领域说明：负责用户账号、登录会话、认证令牌和第三方身份关联。
# 文件职责：测试文件。固定模块关键行为，帮助持续迭代时发现回归。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

import unittest
from datetime import date

from app.db.session import SessionLocal
from app.modules.identity.enums import Gender
from app.modules.identity.exceptions import UserAlreadyExistsError
from app.modules.identity import service as identity_service


# 类职责：IdentityServiceTestCase 承载 用户身份模块 中的一组相关状态或行为。
# 设计边界：保持职责集中，避免把跨模块编排逻辑塞进单个类型。继承/混入：TestCase。
class IdentityServiceTestCase(unittest.TestCase):
    # 函数职责：业务函数，封装 用户身份模块 中的一段可复用逻辑。
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

    # 函数职责：业务函数，封装 用户身份模块 中的一段可复用逻辑。
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
    def test_create_user_success_does_not_expose_password_hash(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
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

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_duplicate_email_is_rejected(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        identity_service.create_user(
            self.db,
            email="phase04a.duplicate@example.com",
            nickname="First",
        )

        # 上下文说明：在受控资源边界内执行，确保会话、文件或事务被正确释放。
        with self.assertRaises(UserAlreadyExistsError):
            identity_service.create_user(
                self.db,
                email="phase04a.duplicate@example.com",
                nickname="Second",
            )

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_get_user_by_email_and_phone(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
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


# 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
if __name__ == "__main__":
    unittest.main()
