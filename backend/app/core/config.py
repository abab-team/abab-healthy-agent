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
    AUTH_ENABLED: bool = False
    AUTH_DEMO_LOGIN_ENABLED: bool = True
    AUTH_DEMO_HEADER_ENABLED: bool = True
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    CORS_ORIGINS: str = ""
    LLM_ENABLED: bool = False
    LLM_PROVIDER: str = "mock"
    LLM_BASE_URL: str = ""
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "mock-model"
    LLM_TIMEOUT_SECONDS: float = 30.0
    LLM_MAX_TOKENS: int = 512
    LLM_TEMPERATURE: float = 0.2
    DAILY_BRIEF_USE_LLM: bool = False
    LLM_PLANNER_ENABLED: bool = False
    LLM_ANSWER_COMPOSER_ENABLED: bool = False
    LLM_CHAT_ENABLED: bool = True
    RULE_CRITIC_ENABLED: bool = True
    LLM_CRITIC_ENABLED: bool = False
    LLM_PLANNER_CONFIDENCE_THRESHOLD: float = 0.75
    PROMPT_REGISTRY_ENABLED: bool = True
    RAG_ENABLED: bool = False
    RAG_PROVIDER: str = "simple"
    RAG_INDEX_INTERNAL_SOURCES: bool = True
    RAG_ALLOW_EXTERNAL_KNOWLEDGE: bool = False
    RAG_MAX_CHUNK_CHARS: int = 1200
    RAG_TOP_K: int = 5
    RAG_STORE_RAW_TEXT: bool = False
    RAG_EMBEDDING_PROVIDER: str = "mock"
    RAG_RETRIEVAL_PROVIDER: str = "simple"
    RAG_MIN_SCORE: float = 0.0
    LANGGRAPH_ENABLED: bool = False
    LANGGRAPH_CHAT_QUERY_ENABLED: bool = False
    LANGGRAPH_DAILY_BRIEF_ENABLED: bool = False
    LANGGRAPH_FREE_TEXT_RECORD_ENABLED: bool = False
    LANGGRAPH_DOCTOR_VISIT_SUMMARY_ENABLED: bool = False
    LANGGRAPH_DOCUMENT_EXTRACT_ENABLED: bool = False
    LANGGRAPH_DAILY_REPORT_ENABLED: bool = False
    LANGGRAPH_HEALTH_KNOWLEDGE_QA_ENABLED: bool = False
    LANGGRAPH_ALERT_CREATE_ENABLED: bool = False
    LANGGRAPH_SYMPTOM_DRAFT_CREATE_ENABLED: bool = False
    LANGGRAPH_MEDICAL_EVENT_DRAFT_CREATE_ENABLED: bool = False
    LANGGRAPH_STRICT_MODE: bool = False
    LANGGRAPH_TRACE_NODE_SUMMARY: bool = True
    DOCUMENT_UPLOAD_ENABLED: bool = True
    DOCUMENT_MAX_UPLOAD_MB: int = 10
    DOCUMENT_STORAGE_BACKEND: str = "local"
    DOCUMENT_STORAGE_DIR: str = "backend/storage/documents"
    DOCUMENT_ALLOWED_MIME_TYPES: str = "application/pdf,image/png,image/jpeg"
    OCR_ENABLED: bool = False
    OCR_PROVIDER: str = "mock"
    OCR_TIMEOUT_SECONDS: float = 30.0
    OCR_MAX_TEXT_CHARS: int = 8000
    OCR_STORE_RAW_TEXT: bool = False
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

    @property
    def document_allowed_mime_types(self) -> set[str]:
        if not self.DOCUMENT_ALLOWED_MIME_TYPES:
            return set()
        return {
            mime.strip().lower()
            for mime in self.DOCUMENT_ALLOWED_MIME_TYPES.split(",")
            if mime.strip()
        }


# 函数职责：配置读取函数，集中加载环境变量和默认配置，供应用启动和业务模块使用。
# 业务边界：配置入口要保持可缓存、可测试，避免运行过程中频繁重复解析。
@lru_cache
def get_settings() -> Settings:
    # 流程说明：
    # 1. 接收查询条件并标准化过滤范围。
    # 2. 从数据库、缓存或下游服务读取当前可信数据。
    # 3. 把查询结果交给调用方进行业务解释或展示。
    return Settings()
