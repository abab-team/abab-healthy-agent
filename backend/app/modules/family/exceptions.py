# 类职责：FamilyError 表示 家庭成员模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：Exception。
# 模块领域：家庭成员模块
# 领域说明：负责家庭、成员关系、邀请流程和自然语言成员称呼解析。
# 文件职责：异常文件。定义领域内可预期的业务错误，便于上层统一转成可读错误响应。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

class FamilyError(Exception):
    """Base family service error."""


# 类职责：FamilyNotFoundError 表示 家庭成员模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：FamilyError。
class FamilyNotFoundError(FamilyError):
    """Raised when a family cannot be found."""


# 类职责：FamilyMemberNotFoundError 表示 家庭成员模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：FamilyError。
class FamilyMemberNotFoundError(FamilyError):
    """Raised when a family member cannot be found."""


# 类职责：FamilyMemberAlreadyExistsError 表示 家庭成员模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：FamilyError。
class FamilyMemberAlreadyExistsError(FamilyError):
    """Raised when a user is already a member of a family."""


class UserAlreadyInFamilyError(FamilyError):
    """Raised when the single-family product mode would be exceeded."""


class InvitationNotAvailableError(FamilyError):
    """Raised when an invitation code is invalid, expired, or already used."""


# 类职责：MemberReferenceNotFoundError 表示 家庭成员模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：FamilyError。
class MemberReferenceNotFoundError(FamilyError):
    """Raised when a family member reference cannot be resolved."""


# 类职责：MemberReferenceAmbiguousError 表示 家庭成员模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：FamilyError。
class MemberReferenceAmbiguousError(FamilyError):
    """Raised when a family member reference matches multiple members."""
