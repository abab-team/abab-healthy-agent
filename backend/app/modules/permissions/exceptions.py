# 类职责：PermissionError 表示 权限模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：Exception。
# 模块领域：权限模块
# 领域说明：负责家庭成员之间的数据共享范围、访问策略和越权拦截。
# 文件职责：异常文件。定义领域内可预期的业务错误，便于上层统一转成可读错误响应。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

class PermissionError(Exception):
    """Base permission service error."""


# 类职责：PermissionDeniedError 表示 权限模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：PermissionError。
class PermissionDeniedError(PermissionError):
    """Raised when permission check fails."""


# 类职责：PermissionNotConfiguredError 表示 权限模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：PermissionError。
class PermissionNotConfiguredError(PermissionError):
    """Raised when target member share permissions are missing."""
