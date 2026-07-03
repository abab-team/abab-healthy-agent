# 模块领域：家庭健康 Agent 通用模块
# 领域说明：承载项目中暂未细分到具体领域的通用能力。
# 文件职责：应用入口文件。创建 FastAPI 应用，挂载中间件、异常处理和路由。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging


# 函数职责：应用构建函数，创建 FastAPI 应用并注册全局配置、异常处理、中间件和路由。
# 业务边界：应用入口只做装配，不承载具体业务逻辑。
def create_app() -> FastAPI:
    # 流程说明：
    # 1. 校验创建请求和必要上下文。
    # 2. 构造新的领域对象并交给仓储层保存。
    # 3. 返回创建后的对象或业务摘要。
    settings = get_settings()
    setup_logging(debug=settings.DEBUG)

    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
    )

    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    register_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
