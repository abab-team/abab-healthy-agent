# 模块领域：健康报告模块
# 领域说明：负责日报、周报、家庭汇总和就医摘要的生成与渲染。
# 文件职责：数据模型文件。定义数据库表、字段、索引和表之间的关系，是业务数据持久化的核心。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from datetime import date
from enum import StrEnum
from uuid import UUID

from sqlalchemy import JSON, Date, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.reports.enums import (
    DailyReportGeneratedBy,
    DailyReportGenerationStatus,
    DailyReportStatusLevel,
)


# 函数职责：业务函数，封装 健康报告模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return [item.value for item in enum_cls]


# 类职责：DailyReport 是 健康报告模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class DailyReport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "daily_reports"

    # 字段说明：user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 字段说明：family_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 字段说明：report_date 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    # 字段说明：overall_status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    overall_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 字段说明：status_level 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    status_level: Mapped[DailyReportStatusLevel] = mapped_column(
        Enum(
            DailyReportStatusLevel,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=DailyReportStatusLevel.INSUFFICIENT_DATA,
    )
    # 字段说明：summary_text 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 字段说明：highlights 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    highlights: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    # 字段说明：concerns 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    concerns: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    # 字段说明：suggestions 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    suggestions: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    # 字段说明：metrics_snapshot 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    metrics_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # 字段说明：related_symptom_record_ids 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    related_symptom_record_ids: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    # 字段说明：related_alert_ids 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    related_alert_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    # 字段说明：generated_by 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    generated_by: Mapped[DailyReportGeneratedBy] = mapped_column(
        Enum(
            DailyReportGeneratedBy,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=DailyReportGeneratedBy.SYSTEM,
    )
    # 字段说明：generation_status 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    generation_status: Mapped[DailyReportGenerationStatus] = mapped_column(
        Enum(
            DailyReportGenerationStatus,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=DailyReportGenerationStatus.PENDING,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "report_date", name="uq_daily_reports_user_id_report_date"),
        Index("ix_daily_reports_user_id", "user_id"),
        Index("ix_daily_reports_family_id", "family_id"),
        Index("ix_daily_reports_report_date", "report_date"),
        Index("ix_daily_reports_status_level", "status_level"),
        Index("ix_daily_reports_generation_status", "generation_status"),
        Index("ix_daily_reports_created_at", "created_at"),
    )
