# 类职责：HealthDataError 表示 健康指标模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：Exception。
# 模块领域：健康指标模块
# 领域说明：负责血压、体重、睡眠、活动等可量化指标的录入、查询和统计。
# 文件职责：异常文件。定义领域内可预期的业务错误，便于上层统一转成可读错误响应。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

class HealthDataError(Exception):
    """Base health data service error."""


# 类职责：HealthMetricNotFoundError 表示 健康指标模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：HealthDataError。
class HealthMetricNotFoundError(HealthDataError):
    """Raised when a metric cannot be found."""


# 类职责：BloodPressureRecordNotFoundError 表示 健康指标模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：HealthDataError。
class BloodPressureRecordNotFoundError(HealthDataError):
    """Raised when a blood pressure record cannot be found."""


# 类职责：InvalidMetricValueError 表示 健康指标模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：HealthDataError。
class InvalidMetricValueError(HealthDataError):
    """Raised when a metric value is invalid."""


# 类职责：InvalidBloodPressureValueError 表示 健康指标模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：HealthDataError。
class InvalidBloodPressureValueError(HealthDataError):
    """Raised when a blood pressure value is invalid."""


# 类职责：HealthDataImportJobNotFoundError 表示 健康指标模块 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：HealthDataError。
class HealthDataImportJobNotFoundError(HealthDataError):
    """Raised when an import job cannot be found."""
