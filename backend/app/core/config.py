# 模块领域：核心基础设施层
# 领域说明：负责配置、环境、日志、异常等横切能力。
# 文件职责：配置文件。集中读取环境变量和默认配置，避免配置散落在业务代码中。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


# 类职责：Settings 承载 核心基础设施层 中的一组相关状态或行为。
# 设计边界：保持职责集中，避免把跨模块编排逻辑塞进单个类型。继承/混入：BaseSettings。
class Settings(BaseSettings):
    # 类内部说明：
    # 1. 类属性描述该领域对象的核心状态。
    # 2. 类方法只处理与该类型强相关的局部行为。
    # 3. 跨对象编排应放在 service、workflow 或 policy 中。
    APP_NAME: str = "family-health-agent"
    ENV: str = "development"
    DEBUG: bool = False
    DATABASE_URL: str = ""
    REDIS_URL: str = ""
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = ""
    LLM_PROVIDER: str = "mock"
    OPENAI_API_KEY: str = ""
    LOCAL_STORAGE_DIR: str = "backend/storage/local"
    S3_ENDPOINT: str = ""
    S3_BUCKET: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    POSTGRES_DB: str = "family_health"
    POSTGRES_USER: str = "family_health"
    POSTGRES_PASSWORD: str = "family_health"
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin"
    DAILY_REPORT_HOUR: int = 8

    model_config = SettingsConfigDict(
        env_file=(
            PROJECT_ROOT / ".env",
            BACKEND_DIR / ".env",
        ),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # 函数职责：业务函数，封装 核心基础设施层 中的一段可复用逻辑。
    # 业务边界：调用方应根据返回值和异常语义处理成功与失败。
    @property
    def cors_origins(self) -> list[str]:
        # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
        # 流程说明：
        # 1. 接收上游传入的数据或上下文。
        # 2. 完成本函数职责范围内的处理。
        # 3. 将结果返回给调用方，继续由上层流程编排。
        if not self.CORS_ORIGINS:
            return []
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


# 函数职责：配置读取函数，集中加载环境变量和默认配置，供应用启动和业务模块使用。
# 业务边界：配置入口要保持可缓存、可测试，避免运行过程中频繁重复解析。
@lru_cache
def get_settings() -> Settings:
    # 流程说明：
    # 1. 接收查询条件并标准化过滤范围。
    # 2. 从数据库、缓存或下游服务读取当前可信数据。
    # 3. 把查询结果交给调用方进行业务解释或展示。
    return Settings()
