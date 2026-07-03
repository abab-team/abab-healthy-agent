# 模块领域：用户身份模块
# 领域说明：负责用户账号、登录会话、认证令牌和第三方身份关联。
# 文件职责：数据结构文件。定义服务层/API 的输入输出对象，隔离外部请求与内部 ORM 模型。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from app.modules.identity.enums import Gender, UserStatus
from app.modules.identity.models import User


# 类职责：UserPublic 是 用户身份模块 的数据传输结构，用于接口入参、出参或服务层结果。
# 设计边界：Schema 负责数据形状和校验，不直接访问数据库。
@dataclass(frozen=True)
class UserPublic:
    # 字段说明：id 是接口/服务层数据结构中的一个显式字段。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    id: UUID
    # 字段说明：phone 是接口/服务层数据结构中的一个显式字段。
    phone: str | None
    # 字段说明：email 是接口/服务层数据结构中的一个显式字段。
    email: str | None
    # 字段说明：nickname 是接口/服务层数据结构中的一个显式字段。
    nickname: str | None
    # 字段说明：avatar_url 是接口/服务层数据结构中的一个显式字段。
    avatar_url: str | None
    # 字段说明：gender 是接口/服务层数据结构中的一个显式字段。
    gender: Gender | None
    # 字段说明：birth_date 是接口/服务层数据结构中的一个显式字段。
    birth_date: date | None
    # 字段说明：status 是接口/服务层数据结构中的一个显式字段。
    status: UserStatus
    # 字段说明：created_at 是接口/服务层数据结构中的一个显式字段。
    created_at: datetime
    # 字段说明：updated_at 是接口/服务层数据结构中的一个显式字段。
    updated_at: datetime
    # 字段说明：last_login_at 是接口/服务层数据结构中的一个显式字段。
    last_login_at: datetime | None


# 函数职责：业务函数，封装 用户身份模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def to_user_public(user: User) -> UserPublic:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return UserPublic(
        id=user.id,
        phone=user.phone,
        email=user.email,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        gender=user.gender,
        birth_date=user.birth_date,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )
