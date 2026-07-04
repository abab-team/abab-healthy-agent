# 模块领域：数据库基础层
# 领域说明：负责 ORM 基类、会话、事务和迁移元数据。
# 文件职责：数据库会话文件。创建 SQLAlchemy 引擎、会话工厂和请求级数据库依赖。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

DEFAULT_DATABASE_URL = "sqlite+pysqlite:///:memory:"

settings = get_settings()
database_url = settings.DATABASE_URL or DEFAULT_DATABASE_URL
engine_kwargs = {
    "pool_pre_ping": True,
    "future": True,
}
if database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
if database_url in {"sqlite+pysqlite:///:memory:", "sqlite:///:memory:", "sqlite://"}:
    engine_kwargs["poolclass"] = StaticPool

engine = create_engine(
    database_url,
    **engine_kwargs,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


# 函数职责：数据库会话函数，提供数据库会话生命周期，保证使用后正确提交、回滚或关闭。
# 业务边界：会话边界必须清晰，避免连接泄漏或跨请求复用脏状态。
def get_db() -> Generator[Session, None, None]:
    # 流程说明：
    # 1. 接收查询条件并标准化过滤范围。
    # 2. 从数据库、缓存或下游服务读取当前可信数据。
    # 3. 把查询结果交给调用方进行业务解释或展示。
    db = SessionLocal()
    # 异常说明：把可能失败的外部调用或底层操作收敛到可控错误路径。
    try:
        yield db
    finally:
        db.close()
