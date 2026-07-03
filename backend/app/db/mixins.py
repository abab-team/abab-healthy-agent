# 模块领域：数据库基础层
# 领域说明：负责 ORM 基类、会话、事务和迁移元数据。
# 文件职责：ORM 通用字段文件。提供主键、时间戳、软删除等各表复用字段。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column


# 函数职责：业务函数，封装 数据库基础层 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def utc_now() -> datetime:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return datetime.now(timezone.utc)


# 类职责：UUIDPrimaryKeyMixin 承载 数据库基础层 中的一组相关状态或行为。
# 设计边界：保持职责集中，避免把跨模块编排逻辑塞进单个类型。
class UUIDPrimaryKeyMixin:
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )


# 类职责：TimestampMixin 承载 数据库基础层 中的一组相关状态或行为。
# 设计边界：保持职责集中，避免把跨模块编排逻辑塞进单个类型。
class TimestampMixin:
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


# 类职责：SoftDeleteMixin 承载 数据库基础层 中的一组相关状态或行为。
# 设计边界：保持职责集中，避免把跨模块编排逻辑塞进单个类型。
class SoftDeleteMixin:
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
