# 模块领域：健康档案模块
# 领域说明：负责家庭成员基础健康信息、长期档案摘要和健康画像。
# 文件职责：测试文件。固定模块关键行为，帮助持续迭代时发现回归。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

import unittest

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.modules.health_profile import service as health_profile_service
from app.modules.health_profile.models import HealthProfile
from app.modules.identity import service as identity_service


# 类职责：HealthProfileServiceTestCase 承载 健康档案模块 中的一组相关状态或行为。
# 设计边界：保持职责集中，避免把跨模块编排逻辑塞进单个类型。继承/混入：TestCase。
class HealthProfileServiceTestCase(unittest.TestCase):
    # 函数职责：业务函数，封装 健康档案模块 中的一段可复用逻辑。
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
        self.user = identity_service.create_user(
            self.db,
            email="phase04b.profile.user@example.com",
            phone="p04b_profile_user",
            nickname="Profile User",
        )

    # 函数职责：业务函数，封装 健康档案模块 中的一段可复用逻辑。
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
    def test_ensure_profile_creates_empty_profile(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        profile = health_profile_service.ensure_profile(self.db, self.user.id)

        self.assertEqual(profile.user_id, self.user.id)
        self.assertIsNone(profile.health_goal)

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_create_or_update_profile_updates_goal(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        profile = health_profile_service.create_or_update_profile(
            self.db,
            self.user.id,
            {"health_goal": "保持规律睡眠"},
        )

        self.assertEqual(profile.health_goal, "保持规律睡眠")

        updated = health_profile_service.create_or_update_profile(
            self.db,
            self.user.id,
            {"health_goal": "每周步行三次"},
        )

        self.assertEqual(updated.id, profile.id)
        self.assertEqual(updated.health_goal, "每周步行三次")

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_ensure_profile_is_idempotent(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        first = health_profile_service.ensure_profile(self.db, self.user.id)
        second = health_profile_service.ensure_profile(self.db, self.user.id)

        count = self.db.scalar(
            select(func.count())
            .select_from(HealthProfile)
            .where(HealthProfile.user_id == self.user.id),
        )

        self.assertEqual(first.id, second.id)
        self.assertEqual(count, 1)

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_profile_snapshot_excludes_identity_sensitive_fields(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        snapshot = health_profile_service.get_profile_snapshot(self.db, self.user.id)

        self.assertEqual(snapshot.user_id, self.user.id)
        self.assertFalse(hasattr(snapshot, "email"))
        self.assertFalse(hasattr(snapshot, "phone"))
        self.assertFalse(hasattr(snapshot, "password_hash"))


# 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
if __name__ == "__main__":
    unittest.main()
