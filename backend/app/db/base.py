# 模块领域：数据库基础层
# 领域说明：负责 ORM 基类、会话、事务和迁移元数据。
# 文件职责：ORM 元数据入口。汇总所有模型，确保 Alembic 能发现完整表结构。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from sqlalchemy.orm import DeclarativeBase


# 类职责：Base 承载 数据库基础层 中的一组相关状态或行为。
# 设计边界：保持职责集中，避免把跨模块编排逻辑塞进单个类型。继承/混入：DeclarativeBase。
class Base(DeclarativeBase):
    """Shared SQLAlchemy declarative base for future ORM models."""

    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    pass


from app.modules.identity import models as identity_models  # noqa: E402,F401
from app.modules.family import models as family_models  # noqa: E402,F401
from app.modules.permissions import models as permission_models  # noqa: E402,F401
from app.modules.health_profile import models as health_profile_models  # noqa: E402,F401
from app.modules.health_data import models as health_data_models  # noqa: E402,F401
from app.modules.health_record import models as health_record_models  # noqa: E402,F401
from app.modules.medical_timeline import models as medical_timeline_models  # noqa: E402,F401
from app.modules.document_center import models as document_center_models  # noqa: E402,F401
from app.modules.document_processing import models as document_processing_models  # noqa: E402,F401
from app.modules.reports import models as report_models  # noqa: E402,F401
from app.modules.alerts import models as alert_models  # noqa: E402,F401
from app.agent import models as agent_models  # noqa: E402,F401
from app.modules.audit import models as audit_models  # noqa: E402,F401
