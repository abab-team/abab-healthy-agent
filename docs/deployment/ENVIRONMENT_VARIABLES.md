# 环境变量说明

本文档列出 MVP 演示部署需要关注的环境变量。`.env.example` 只允许存放占位值；真实 `.env`、API key、JWT secret 不得提交。

## 应用与运行环境

| 变量 | 默认建议 | 说明 |
| --- | --- | --- |
| `APP_NAME` | `family-health-agent` | 服务名。 |
| `ENV` / `APP_ENV` | `development` | 当前运行环境。代码使用 `ENV`，`APP_ENV` 作为部署文档别名。 |
| `DEBUG` | `false` in production | 生产必须关闭。 |

## 数据库与缓存

| 变量 | 默认建议 | 说明 |
| --- | --- | --- |
| `DATABASE_URL` | 本地 SQLite 或 dev PostgreSQL | 演示可用 SQLite；生产建议 PostgreSQL。 |
| `REDIS_URL` | `redis://localhost:6379/0` | 预留缓存/任务队列。 |

## Auth/JWT

| 变量 | 生产建议 | 说明 |
| --- | --- | --- |
| `AUTH_ENABLED` | `true` | 启用认证能力。 |
| `AUTH_DEMO_LOGIN_ENABLED` | 按需关闭 | demo login 仅用于演示。 |
| `AUTH_DEMO_HEADER_ENABLED` | `false` | 生产必须关闭 `X-Current-User-Id` fallback。 |
| `SECRET_KEY` | 强随机值 | 通用签名密钥占位。 |
| `JWT_SECRET_KEY` | 强随机值 | JWT 签名密钥，不能使用示例值。 |
| `JWT_ALGORITHM` | `HS256` | 当前最小实现。 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | 访问令牌过期时间。 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | refresh token 过期时间。 |

## CORS

| 变量 | 生产建议 | 说明 |
| --- | --- | --- |
| `CORS_ORIGINS` / `CORS_ALLOW_ORIGINS` | 明确域名 | 当前代码读取 `CORS_ORIGINS`；部署文档中 `CORS_ALLOW_ORIGINS` 仅作为语义别名说明。不要使用 `*`。 |

## LLM

| 变量 | 默认建议 | 说明 |
| --- | --- | --- |
| `LLM_ENABLED` | `false` | 默认关闭。 |
| `LLM_PROVIDER` | `mock` | 默认 mock。 |
| `LLM_BASE_URL` | 空 | OpenAI-compatible endpoint，仅本地 `.env` 填写。 |
| `LLM_API_KEY` | 空 | 不得提交真实 key。 |
| `LLM_MODEL` | `mock-model` | mock 或真实模型名。 |
| `DAILY_BRIEF_USE_LLM` | `false` | 只有同时开启 `LLM_ENABLED=true` 才会影响 daily brief。 |

## OCR 与文档

| 变量 | 默认建议 | 说明 |
| --- | --- | --- |
| `DOCUMENT_UPLOAD_ENABLED` | `true` | 控制文档上传入口。 |
| `DOCUMENT_STORAGE_DIR` | `backend/storage/documents` | 本地 storage 目录，不提交内容。 |
| `DOCUMENT_MAX_UPLOAD_MB` | `10` | 上传大小上限。 |
| `OCR_ENABLED` | `false` | 默认关闭。 |
| `OCR_PROVIDER` | `mock` | 当前仅 mock OCR。 |
| `OCR_STORE_RAW_TEXT` | `false` | 默认不存完整 raw OCR。 |

## RAG

| 变量 | 默认建议 | 说明 |
| --- | --- | --- |
| `RAG_ENABLED` | `false` | 默认关闭。 |
| `RAG_PROVIDER` | `simple` | 当前 simple/internal retrieval。 |
| `RAG_ALLOW_EXTERNAL_KNOWLEDGE` | `false` | 不接外部医学知识库。 |
| `RAG_STORE_RAW_TEXT` | `false` | 不索引 raw text / raw OCR。 |
| `RAG_TOP_K` | `5` | 默认检索数量。 |

## 移动端

在 `apps/mobile/.env` 中配置：

```text
EXPO_PUBLIC_DATA_MODE=mock|api|api-auth
EXPO_PUBLIC_AUTH_MODE=demo|auth
EXPO_PUBLIC_API_BASE_URL=http://<电脑局域网IP>:8000
EXPO_PUBLIC_DEMO_USER_ID=<demo user uuid>
```

Expo Go 真机不能使用 `localhost`。

