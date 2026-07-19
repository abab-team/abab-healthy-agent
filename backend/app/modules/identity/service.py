# 模块领域：用户身份模块
# 领域说明：负责用户账号、登录会话、认证令牌和第三方身份关联。
# 文件职责：业务服务文件。编排领域规则、权限校验、仓储调用和状态流转，是模块的主要业务入口。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.identity import repository
from app.modules.identity import avatar_storage
from app.core.config import Settings
from app.modules.identity.enums import Gender, UserStatus
from app.modules.identity.exceptions import (
    UserAlreadyExistsError,
    UserContactRequiredError,
    UserNotFoundError,
)
from app.modules.identity.models import User
from app.modules.identity.schemas import UserPublic, to_user_public


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
) -> UserPublic:
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    if email is None and phone is None:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise UserContactRequiredError("email or phone is required to create a user")
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if email is not None and repository.get_user_by_email(db, email) is not None:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise UserAlreadyExistsError("email already exists")
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if phone is not None and repository.get_user_by_phone(db, phone) is not None:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise UserAlreadyExistsError("phone already exists")

    user = repository.create_user(
        db,
        email=email,
        phone=phone,
        nickname=nickname,
        password_hash=password_hash,
        gender=gender,
        birth_date=birth_date,
        status=status,
    )
    return to_user_public(user)


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_user(db: Session, user_id: UUID) -> UserPublic | None:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    user = repository.get_user_by_id(db, user_id)
    return to_user_public(user) if user is not None else None


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_user_by_email(db: Session, email: str) -> UserPublic | None:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    user = repository.get_user_by_email(db, email)
    return to_user_public(user) if user is not None else None


# 函数职责：查询流程，根据业务标识读取对象或聚合信息。
# 业务边界：查询函数只负责返回当前可信数据，不在这里做跨模块副作用。
def get_user_by_phone(db: Session, phone: str) -> UserPublic | None:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    user = repository.get_user_by_phone(db, phone)
    return to_user_public(user) if user is not None else None


# 函数职责：校验流程，集中执行前置条件检查，失败时抛出领域异常。
# 业务边界：校验函数不应偷偷修改业务状态，便于调用方预测副作用。
def ensure_user_exists(db: Session, user_id: UUID) -> User:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    user = repository.get_user_by_id(db, user_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if user is None:
        # 异常抛出：当前业务条件不满足，主动中断流程并交给上层处理。
        raise UserNotFoundError("user not found")
    return user


# 函数职责：更新流程，在校验当前状态后修改已有对象或推进状态机。
# 业务边界：更新动作要保持幂等性和状态合法性，避免跳过必要确认。
def update_profile(
    db: Session,
    user_id: UUID,
    *,
    nickname: str | None = None,
    avatar_url: str | None = None,
    gender: Gender | None = None,
    birth_date: date | None = None,
) -> UserPublic:
    # 流程说明：
    # 1. 接收接口层或其他模块传入的业务请求。
    # 2. 按模块规则完成校验、权限判断和状态流转。
    # 3. 调用仓储层读写数据，并返回稳定的业务结果。
    user = ensure_user_exists(db, user_id)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if nickname is not None:
        user.nickname = nickname
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if avatar_url is not None:
        user.avatar_url = avatar_url
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if gender is not None:
        user.gender = gender
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if birth_date is not None:
        user.birth_date = birth_date
    db.flush()
    return to_user_public(user)


def upload_avatar(db: Session, user_id: UUID, *, content: bytes, mime_type: str | None, settings: Settings) -> UserPublic:
    user = ensure_user_exists(db, user_id)
    avatar_storage.store_avatar_bytes(
        content=content,
        mime_type=mime_type,
        settings=settings,
        user_id=user_id,
    )
    user.avatar_url = f"/api/v1/identity/users/{user_id}/avatar"
    db.flush()
    return to_user_public(user)
