# 模块领域：用户身份模块
# 领域说明：负责用户账号、登录会话、认证令牌和第三方身份关联。
# 文件职责：仓储文件。封装数据库查询和写入细节，让业务服务只表达业务意图。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.identity.enums import Gender, UserStatus
from app.modules.identity.models import User


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    return db.get(User, user_id)


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_user_by_email(db: Session, email: str) -> User | None:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    return db.scalar(select(User).where(User.email == email))


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_user_by_phone(db: Session, phone: str) -> User | None:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    return db.scalar(select(User).where(User.phone == phone))


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def create_user(
    db: Session,
    *,
    email: str | None = None,
    phone: str | None = None,
    nickname: str | None = None,
    password_hash: str | None = None,
    gender: Gender | None = None,
    birth_date: date | None = None,
    status: UserStatus = UserStatus.ACTIVE,
) -> User:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    user = User(
        email=email,
        phone=phone,
        nickname=nickname,
        password_hash=password_hash,
        gender=gender,
        birth_date=birth_date,
        status=status,
    )
    db.add(user)
    db.flush()
    return user


# 函数职责：更新流程，在校验当前状态后修改已有对象或推进状态机。
# 业务边界：更新动作要保持幂等性和状态合法性，避免跳过必要确认。
def update_last_login_at(
    db: Session,
    user_id: UUID,
    login_at: datetime,
) -> User | None:
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    user = get_user_by_id(db, user_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if user is None:
        return None
    user.last_login_at = login_at
    db.flush()
    return user


# 函数职责：列表查询流程，按过滤条件返回一组对象，并保持排序、分页或范围语义稳定。
# 业务边界：返回集合时要避免把未授权数据暴露给调用方。
def list_users_by_ids(db: Session, user_ids: list[UUID]) -> list[User]:
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    # 流程说明：
    # 1. 接收服务层传入的查询或写入条件。
    # 2. 使用统一数据库会话执行 ORM 操作。
    # 3. 返回 ORM 对象或基础结果，由服务层继续处理业务语义。
    if not user_ids:
        return []
    return list(db.scalars(select(User).where(User.id.in_(user_ids))))
