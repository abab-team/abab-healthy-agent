# 模块领域：健康记录模块
# 领域说明：负责症状、用药、就医、备注等事件型健康记录。
# 文件职责：测试文件。固定模块关键行为，帮助持续迭代时发现回归。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

import unittest

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.modules.health_data.models import BloodPressureRecord
from app.modules.health_record import service as health_record_service
from app.modules.health_record.enums import HealthRecordDraftStatus, SymptomRecordStatus
from app.modules.health_record.exceptions import (
    HealthRecordDraftNotPendingError,
    InvalidHealthRecordDraftError,
)
from app.modules.health_record.models import HealthRecordDraft, SymptomRecord
from app.modules.identity import service as identity_service


# 类职责：HealthRecordServiceTestCase 承载 健康记录模块 中的一组相关状态或行为。
# 设计边界：保持职责集中，避免把跨模块编排逻辑塞进单个类型。继承/混入：TestCase。
class HealthRecordServiceTestCase(unittest.TestCase):
    # 函数职责：业务函数，封装 健康记录模块 中的一段可复用逻辑。
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
            email="phase04b.health_record.user@example.com",
            phone="p04b_record_user",
            nickname="Health Record User",
        )

    # 函数职责：业务函数，封装 健康记录模块 中的一段可复用逻辑。
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
    def test_create_symptom_record_success(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        record = health_record_service.create_symptom_record(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            raw_text="今天头痛两小时",
            symptom_name="头痛",
            follow_up_needed=True,
        )

        self.assertEqual(record.user_id, self.user.id)
        self.assertEqual(record.symptom_name, "头痛")
        self.assertTrue(record.follow_up_needed)

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_create_symptom_record_requires_raw_text(self) -> None:
        # 上下文说明：在受控资源边界内执行，确保会话、文件或事务被正确释放。
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        with self.assertRaises(InvalidHealthRecordDraftError):
            health_record_service.create_symptom_record(
                self.db,
                user_id=self.user.id,
                created_by_user_id=self.user.id,
                raw_text=" ",
            )

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_recent_symptoms_and_summary(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        health_record_service.create_symptom_record(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            raw_text="最近咳嗽",
            symptom_name="咳嗽",
            follow_up_needed=True,
        )

        records = health_record_service.get_recent_symptoms(
            self.db,
            user_id=self.user.id,
        )
        summary = health_record_service.get_symptom_summary(
            self.db,
            user_id=self.user.id,
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(summary.count, 1)
        self.assertEqual(summary.active_count, 1)
        self.assertEqual(summary.follow_up_needed_count, 1)
        self.assertFalse(hasattr(summary, "diagnosis"))

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_confirm_symptom_draft_creates_symptom_record(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        draft = health_record_service.create_health_record_draft(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            raw_text="昨晚胃痛，持续半小时",
            extracted_json={
                "symptom": {
                    "symptom_name": "胃痛",
                    "body_part": "腹部",
                    "duration_text": "半小时",
                    "follow_up_needed": True,
                    "ai_summary": "用户确认前的结构化草稿",
                },
            },
        )

        record = health_record_service.confirm_symptom_draft(
            self.db,
            draft_id=draft.id,
            confirmed_by_user_id=self.user.id,
        )
        refreshed_draft = self.db.get(HealthRecordDraft, draft.id)

        self.assertEqual(record.symptom_name, "胃痛")
        self.assertEqual(record.source.value, "ai_extracted")
        self.assertEqual(refreshed_draft.status, HealthRecordDraftStatus.CONFIRMED)
        self.assertEqual(refreshed_draft.confirmed_record_id, record.id)

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_confirmed_draft_cannot_be_confirmed_twice(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        draft = health_record_service.create_health_record_draft(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            raw_text="头晕",
            extracted_json={"symptom_name": "头晕"},
        )
        health_record_service.confirm_symptom_draft(
            self.db,
            draft_id=draft.id,
            confirmed_by_user_id=self.user.id,
        )

        # 上下文说明：在受控资源边界内执行，确保会话、文件或事务被正确释放。
        with self.assertRaises(HealthRecordDraftNotPendingError):
            health_record_service.confirm_symptom_draft(
                self.db,
                draft_id=draft.id,
                confirmed_by_user_id=self.user.id,
            )

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_cancelled_draft_cannot_be_confirmed(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        draft = health_record_service.create_health_record_draft(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            raw_text="乏力",
            extracted_json={"symptom_name": "乏力"},
        )
        health_record_service.cancel_draft(self.db, draft.id)

        # 上下文说明：在受控资源边界内执行，确保会话、文件或事务被正确释放。
        with self.assertRaises(HealthRecordDraftNotPendingError):
            health_record_service.confirm_symptom_draft(
                self.db,
                draft_id=draft.id,
                confirmed_by_user_id=self.user.id,
            )

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_update_symptom_status(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        record = health_record_service.create_symptom_record(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            raw_text="皮肤瘙痒",
            symptom_name="瘙痒",
        )

        updated = health_record_service.update_symptom_record_status(
            self.db,
            record.id,
            SymptomRecordStatus.RESOLVED,
        )

        self.assertEqual(updated.status, SymptomRecordStatus.RESOLVED)

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_draft_confirmation_does_not_write_blood_pressure(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        draft = health_record_service.create_health_record_draft(
            self.db,
            user_id=self.user.id,
            created_by_user_id=self.user.id,
            raw_text="血压 120/80，今天有点头痛",
            extracted_json={"symptom_name": "头痛"},
        )
        health_record_service.confirm_symptom_draft(
            self.db,
            draft_id=draft.id,
            confirmed_by_user_id=self.user.id,
        )

        symptom_count = self.db.scalar(
            select(func.count())
            .select_from(SymptomRecord)
            .where(SymptomRecord.user_id == self.user.id),
        )
        pressure_count = self.db.scalar(
            select(func.count())
            .select_from(BloodPressureRecord)
            .where(BloodPressureRecord.user_id == self.user.id),
        )

        self.assertEqual(symptom_count, 1)
        self.assertEqual(pressure_count, 0)


# 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
if __name__ == "__main__":
    unittest.main()
