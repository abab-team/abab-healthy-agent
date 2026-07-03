# 类职责：IdentityError 表示 用户身份模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：Exception。
# 模块领域：用户身份模块
# 领域说明：负责用户账号、登录会话、认证令牌和第三方身份关联。
# 文件职责：异常文件。定义领域内可预期的业务错误，便于上层统一转成可读错误响应。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

class IdentityError(Exception):
    """Base identity service error."""


# 类职责：UserNotFoundError 表示 用户身份模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：IdentityError。
class UserNotFoundError(IdentityError):
    """Raised when a user cannot be found."""


# 类职责：UserAlreadyExistsError 表示 用户身份模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：IdentityError。
class UserAlreadyExistsError(IdentityError):
    """Raised when email or phone is already used by another user."""


# 类职责：UserContactRequiredError 表示 用户身份模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：IdentityError。
class UserContactRequiredError(IdentityError):
    """Raised when creating a user without email or phone."""
