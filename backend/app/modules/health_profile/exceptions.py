# 类职责：HealthProfileError 表示 健康档案模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：Exception。
# 模块领域：健康档案模块
# 领域说明：负责家庭成员基础健康信息、长期档案摘要和健康画像。
# 文件职责：异常文件。定义领域内可预期的业务错误，便于上层统一转成可读错误响应。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

class HealthProfileError(Exception):
    """Base health profile service error."""


# 类职责：HealthProfileNotFoundError 表示 健康档案模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：HealthProfileError。
class HealthProfileNotFoundError(HealthProfileError):
    """Raised when a health profile cannot be found."""


# 类职责：HealthProfileAlreadyExistsError 表示 健康档案模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：HealthProfileError。
class HealthProfileAlreadyExistsError(HealthProfileError):
    """Raised when a user already has a health profile."""
