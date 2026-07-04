# 模块领域：核心基础设施层
# 领域说明：负责配置、环境、日志、异常等横切能力。
# 文件职责：异常文件。定义领域内可预期的业务错误，便于上层统一转成可读错误响应。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import (
    ApiErrorCode,
    build_error_detail,
    business_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.modules.alerts.exceptions import AlertsError
from app.modules.document_center.exceptions import DocumentCenterError
from app.modules.document_processing.exceptions import DocumentProcessingError
from app.modules.family.exceptions import FamilyError
from app.modules.health_data.exceptions import HealthDataError
from app.modules.health_profile.exceptions import HealthProfileError
from app.modules.health_record.exceptions import HealthRecordError
from app.modules.identity.exceptions import IdentityError
from app.modules.medical_timeline.exceptions import MedicalTimelineError
from app.modules.permissions.exceptions import PermissionError as ModulePermissionError
from app.modules.reports.exceptions import ReportsError


# 类职责：AppException 表示 核心基础设施层 中可预期的业务异常。
# 设计边界：领域异常用于表达业务失败，不直接决定 HTTP 状态码。继承/混入：Exception。
class AppException(Exception):
    # 函数职责：业务函数，封装 核心基础设施层 中的一段可复用逻辑。
    # 业务边界：调用方应根据返回值和异常语义处理成功与失败。
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    def __init__(self, message: str, status_code: int = 400) -> None:
        # 流程说明：
        # 1. 接收上游传入的数据或上下文。
        # 2. 完成本函数职责范围内的处理。
        # 3. 将结果返回给调用方，继续由上层流程编排。
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# 函数职责：业务函数，封装 核心基础设施层 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": build_error_detail(
                code=ApiErrorCode.INVALID_REQUEST,
                message=exc.message,
                request_id=request.headers.get("X-Request-Id"),
            ),
        },
    )


# 函数职责：创建流程，完成输入校验、业务规则检查和新对象写入。
# 业务边界：创建动作通常会影响数据库状态，调用前必须保证必要权限和唯一性约束。
def register_exception_handlers(app: FastAPI) -> None:
    # 流程说明：
    # 1. 校验创建请求和必要上下文。
    # 2. 构造新的领域对象并交给仓储层保存。
    # 3. 返回创建后的对象或业务摘要。
    app.add_exception_handler(AppException, app_exception_handler)
    for exception_class in (
        AlertsError,
        DocumentCenterError,
        DocumentProcessingError,
        FamilyError,
        HealthDataError,
        HealthProfileError,
        HealthRecordError,
        IdentityError,
        MedicalTimelineError,
        ModulePermissionError,
        ReportsError,
    ):
        app.add_exception_handler(exception_class, business_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
