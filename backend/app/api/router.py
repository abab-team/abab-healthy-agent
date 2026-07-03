# 模块领域：HTTP API 层
# 领域说明：负责聚合路由、暴露接口和提供服务健康检查。
# 文件职责：路由聚合文件。集中注册各模块路由，避免主入口被业务细节污染。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from fastapi import APIRouter

from app.api.health import router as health_router


api_router = APIRouter()
api_router.include_router(health_router)
