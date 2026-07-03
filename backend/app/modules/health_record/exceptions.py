# 类职责：HealthRecordError 表示 健康记录模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：Exception。
# 模块领域：健康记录模块
# 领域说明：负责症状、用药、就医、备注等事件型健康记录。
# 文件职责：异常文件。定义领域内可预期的业务错误，便于上层统一转成可读错误响应。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

class HealthRecordError(Exception):
    """Base health record service error."""


# 类职责：SymptomRecordNotFoundError 表示 健康记录模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：HealthRecordError。
class SymptomRecordNotFoundError(HealthRecordError):
    """Raised when a symptom record cannot be found."""


# 类职责：HealthRecordDraftNotFoundError 表示 健康记录模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：HealthRecordError。
class HealthRecordDraftNotFoundError(HealthRecordError):
    """Raised when a health record draft cannot be found."""


# 类职责：HealthRecordDraftNotPendingError 表示 健康记录模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：HealthRecordError。
class HealthRecordDraftNotPendingError(HealthRecordError):
    """Raised when a non-pending draft is confirmed."""


# 类职责：HealthRecordDraftTypeUnsupportedError 表示 健康记录模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：HealthRecordError。
class HealthRecordDraftTypeUnsupportedError(HealthRecordError):
    """Raised when a draft type cannot create a symptom record."""


# 类职责：InvalidHealthRecordDraftError 表示 健康记录模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：HealthRecordError。
class InvalidHealthRecordDraftError(HealthRecordError):
    """Raised when draft payload is invalid."""
