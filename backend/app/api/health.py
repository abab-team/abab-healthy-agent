# 模块领域：HTTP API 层
# 领域说明：负责聚合路由、暴露接口和提供服务健康检查。
# 文件职责：健康检查文件。提供服务存活接口，供本地开发、容器编排和监控系统探测。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from fastapi import APIRouter


router = APIRouter()


# 函数职责：业务函数，封装 HTTP API 层 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
@router.get("/health")
def health_check() -> dict[str, str]:
    # 流程说明：
    # 1. 从 HTTP 请求中接收参数和依赖对象。
    # 2. 调用服务层完成实际业务处理。
    # 3. 将服务层结果转换为接口响应，不在接口层堆业务规则。
    return {
        "status": "ok",
        "service": "family-health-agent",
    }
