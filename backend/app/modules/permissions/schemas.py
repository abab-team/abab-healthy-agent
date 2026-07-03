# 模块领域：权限模块
# 领域说明：负责家庭成员之间的数据共享范围、访问策略和越权拦截。
# 文件职责：数据结构文件。定义服务层/API 的输入输出对象，隔离外部请求与内部 ORM 模型。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations

from dataclasses import dataclass


# 类职责：PermissionCheckResult 是 权限模块 的数据传输结构，用于接口入参、出参或服务层结果。
# 设计边界：Schema 负责数据形状和校验，不直接访问数据库。
@dataclass(frozen=True)
class PermissionCheckResult:
    # 字段说明：allowed 是接口/服务层数据结构中的一个显式字段。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    allowed: bool
    # 字段说明：permission_type 是接口/服务层数据结构中的一个显式字段。
    permission_type: str
    # 字段说明：action 是接口/服务层数据结构中的一个显式字段。
    action: str
    # 字段说明：reason 是接口/服务层数据结构中的一个显式字段。
    reason: str
    # 字段说明：visibility_scope 是接口/服务层数据结构中的一个显式字段。
    visibility_scope: str
    # 字段说明：safe_message 是接口/服务层数据结构中的一个显式字段。
    safe_message: str
