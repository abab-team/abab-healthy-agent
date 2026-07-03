# 模块领域：数据库基础层
# 领域说明：负责 ORM 基类、会话、事务和迁移元数据。
# 文件职责：事务文件。封装事务边界，保证成组写入成功提交、失败回滚。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.db.session import SessionLocal


# 函数职责：业务函数，封装 数据库基础层 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
@contextmanager
def transactional_session() -> Iterator[Session]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    db = SessionLocal()
    # 异常说明：把可能失败的外部调用或底层操作收敛到可控错误路径。
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise
    finally:
        db.close()


# 函数职责：业务函数，封装 数据库基础层 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
@contextmanager
def transaction(db: Session) -> Iterator[Session]:
    # 异常说明：把可能失败的外部调用或底层操作收敛到可控错误路径。
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise
