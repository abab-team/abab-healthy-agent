# 模块领域：数据库迁移层
# 领域说明：负责用版本化脚本维护数据库结构变更。
# 文件职责：业务代码文件。承载本模块的一部分领域能力或工程能力。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from logging.config import fileConfig
from pathlib import Path
import os
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402

config = context.config

# 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_database_url() -> str:
    # 流程说明：
    # 1. 接收查询条件并标准化过滤范围。
    # 2. 从数据库、缓存或下游服务读取当前可信数据。
    # 3. 把查询结果交给调用方进行业务解释或展示。
    settings = get_settings()
    return os.getenv("DATABASE_URL") or settings.DATABASE_URL or "sqlite+pysqlite:///:memory:"


# 函数职责：执行流程，串联上下文、依赖服务和结果处理，完成一次完整动作。
# 业务边界：执行函数应清晰记录输入、输出和失败路径，便于审计。
def run_migrations_offline() -> None:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    # 上下文说明：在受控资源边界内执行，确保会话、文件或事务被正确释放。
    with context.begin_transaction():
        context.run_migrations()


# 函数职责：执行流程，串联上下文、依赖服务和结果处理，完成一次完整动作。
# 业务边界：执行函数应清晰记录输入、输出和失败路径，便于审计。
def run_migrations_online() -> None:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # 上下文说明：在受控资源边界内执行，确保会话、文件或事务被正确释放。
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        # 上下文说明：在受控资源边界内执行，确保会话、文件或事务被正确释放。
        with context.begin_transaction():
            context.run_migrations()


# 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
