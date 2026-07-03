# 模块领域：健康指标模块
# 领域说明：负责血压、体重、睡眠、活动等可量化指标的录入、查询和统计。
# 文件职责：测试文件。固定模块关键行为，帮助持续迭代时发现回归。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.modules.health_data import service as health_data_service
from app.modules.health_data.enums import MetricType
from app.modules.health_data.exceptions import (
    InvalidBloodPressureValueError,
    InvalidMetricValueError,
)
from app.modules.health_data.models import BloodPressureRecord, HealthMetric
from app.modules.identity import service as identity_service


# 类职责：HealthDataServiceTestCase 承载 健康指标模块 中的一组相关状态或行为。
# 设计边界：保持职责集中，避免把跨模块编排逻辑塞进单个类型。继承/混入：TestCase。
class HealthDataServiceTestCase(unittest.TestCase):
    # 函数职责：业务函数，封装 健康指标模块 中的一段可复用逻辑。
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
            email="phase04b.health_data.user@example.com",
            phone="p04b_data_user",
            nickname="Health Data User",
        )

    # 函数职责：业务函数，封装 健康指标模块 中的一段可复用逻辑。
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
    def test_add_metric_and_recent_metrics(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        metric = health_data_service.add_metric(
            self.db,
            user_id=self.user.id,
            metric_type=MetricType.STEPS,
            value_numeric=8000,
            unit="steps",
        )

        records = health_data_service.get_recent_metrics(
            self.db,
            user_id=self.user.id,
            metric_types=[MetricType.STEPS],
        )

        self.assertEqual(metric.metric_type, MetricType.STEPS)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].id, metric.id)

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_add_metric_requires_value(self) -> None:
        # 上下文说明：在受控资源边界内执行，确保会话、文件或事务被正确释放。
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        with self.assertRaises(InvalidMetricValueError):
            health_data_service.add_metric(
                self.db,
                user_id=self.user.id,
                metric_type=MetricType.SLEEP_DURATION,
            )

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_metric_summary_reports_data_quality_without_health_judgment(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        now = datetime.now(timezone.utc)
        health_data_service.add_metric(
            self.db,
            user_id=self.user.id,
            metric_type=MetricType.SLEEP_DURATION,
            value_numeric=6,
            unit="hour",
            measured_at=now - timedelta(days=2),
        )
        health_data_service.add_metric(
            self.db,
            user_id=self.user.id,
            metric_type=MetricType.SLEEP_DURATION,
            value_numeric=7,
            unit="hour",
            measured_at=now - timedelta(days=1),
        )
        health_data_service.add_metric(
            self.db,
            user_id=self.user.id,
            metric_type=MetricType.SLEEP_DURATION,
            value_numeric=8,
            unit="hour",
            measured_at=now,
        )

        summary = health_data_service.get_metric_summary(
            self.db,
            user_id=self.user.id,
            metric_type=MetricType.SLEEP_DURATION,
        )

        self.assertEqual(summary.count, 3)
        self.assertEqual(summary.latest_value, 8.0)
        self.assertEqual(summary.avg_value, 7.0)
        self.assertEqual(summary.data_quality, "partial")
        self.assertFalse(hasattr(summary, "diagnosis"))
        self.assertFalse(hasattr(summary, "risk_level"))

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_add_blood_pressure_record_and_summary(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        record = health_data_service.add_blood_pressure_record(
            self.db,
            user_id=self.user.id,
            systolic=120,
            diastolic=80,
            pulse=72,
        )

        summary = health_data_service.get_blood_pressure_summary(
            self.db,
            user_id=self.user.id,
        )

        self.assertEqual(record.systolic, 120)
        self.assertEqual(summary.count, 1)
        self.assertEqual(summary.latest_systolic, 120)
        self.assertEqual(summary.latest_diastolic, 80)
        self.assertEqual(summary.data_quality, "insufficient")
        self.assertFalse(hasattr(summary, "diagnosis"))
        self.assertFalse(hasattr(summary, "risk_level"))

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_unreasonable_blood_pressure_value_is_rejected(self) -> None:
        # 上下文说明：在受控资源边界内执行，确保会话、文件或事务被正确释放。
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        with self.assertRaises(InvalidBloodPressureValueError):
            health_data_service.add_blood_pressure_record(
                self.db,
                user_id=self.user.id,
                systolic=20,
                diastolic=80,
            )

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_empty_blood_pressure_summary_means_missing_data_only(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        summary = health_data_service.get_blood_pressure_summary(
            self.db,
            user_id=self.user.id,
        )

        self.assertEqual(summary.count, 0)
        self.assertEqual(summary.data_quality, "missing")
        self.assertIsNone(summary.latest_systolic)
        self.assertFalse(hasattr(summary, "health_status"))

    # 函数职责：测试流程，覆盖一条关键业务行为或边界条件。
    # 业务边界：测试应固定输入输出，帮助后续重构时发现回归问题。
    def test_blood_pressure_does_not_write_health_metrics(self) -> None:
        # 流程说明：
        # 1. 构造固定输入和依赖对象。
        # 2. 执行被测业务函数。
        # 3. 使用断言固定期望结果，避免后续修改破坏行为。
        health_data_service.add_blood_pressure_record(
            self.db,
            user_id=self.user.id,
            systolic=118,
            diastolic=76,
        )

        metric_count = self.db.scalar(
            select(func.count())
            .select_from(HealthMetric)
            .where(HealthMetric.user_id == self.user.id),
        )
        pressure_count = self.db.scalar(
            select(func.count())
            .select_from(BloodPressureRecord)
            .where(BloodPressureRecord.user_id == self.user.id),
        )

        self.assertEqual(metric_count, 0)
        self.assertEqual(pressure_count, 1)


# 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
if __name__ == "__main__":
    unittest.main()
