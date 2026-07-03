# 模块领域：权限模块
# 领域说明：负责家庭成员之间的数据共享范围、访问策略和越权拦截。
# 文件职责：枚举定义文件。集中约束状态、类型、来源等固定取值，避免魔法字符串散落在业务代码中。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from enum import StrEnum


# 类职责：PermissionAuditAction 约束 权限模块 中允许出现的固定状态或类型。
# 设计边界：新增枚举值前要同步检查迁移、接口兼容和前端展示。继承/混入：StrEnum。
class PermissionAuditAction(StrEnum):
    # 枚举说明：GRANT 是该枚举允许出现的一个业务取值。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    GRANT = "grant"
    # 枚举说明：REVOKE 是该枚举允许出现的一个业务取值。
    REVOKE = "revoke"
    # 枚举说明：UPDATE 是该枚举允许出现的一个业务取值。
    UPDATE = "update"
    # 枚举说明：RESET 是该枚举允许出现的一个业务取值。
    RESET = "reset"
