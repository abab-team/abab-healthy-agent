# 模块领域：健康档案模块
# 领域说明：负责家庭成员基础健康信息、长期档案摘要和健康画像。
# 文件职责：数据模型文件。定义数据库表、字段、索引和表之间的关系，是业务数据持久化的核心。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from datetime import date
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.health_profile.enums import BloodType
from app.modules.identity.enums import Gender


# 函数职责：业务函数，封装 健康档案模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return [item.value for item in enum_cls]


# 类职责：HealthProfile 是 健康档案模块 的持久化模型，用来映射数据库表和业务实体。
# 设计边界：模型层只描述字段、关系和基础约束，不承载复杂业务流程。继承/混入：UUIDPrimaryKeyMixin, TimestampMixin, Base。
class HealthProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    __tablename__ = "health_profiles"

    # 字段说明：user_id 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    # 字段说明：height_cm 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    height_cm: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    # 字段说明：gender 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    gender: Mapped[Gender | None] = mapped_column(
        Enum(
            Gender,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=True,
    )
    # 字段说明：birth_date 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # 字段说明：blood_type 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    blood_type: Mapped[BloodType | None] = mapped_column(
        Enum(
            BloodType,
            values_callable=enum_values,
            native_enum=False,
            length=16,
        ),
        nullable=True,
    )
    # 字段说明：health_goal 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    health_goal: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # 字段说明：chronic_conditions_summary 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    chronic_conditions_summary: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    # 字段说明：allergy_summary 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    allergy_summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    # 字段说明：medication_summary 映射数据库字段或关系，用于保存该业务对象的一部分状态。
    medication_summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    __table_args__ = (Index("ix_health_profiles_user_id", "user_id"),)
