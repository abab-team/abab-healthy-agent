# Phase 12 Auth Final Review

## 结论

Phase 12 完成 Auth/JWT 与用户会话基础闭环：

- 后端 Auth API。
- JWT current user dependency。
- demo header fallback 过渡策略。
- 移动端登录态、Authorization header、refresh、logout。
- Auth smoke 与移动端 auth smoke。
- 安全文档和 QA 清单。

## 已完成能力

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- 统一 current user dependency 支持 Bearer token。
- `AUTH_DEMO_HEADER_ENABLED=true` 时保留 `X-Current-User-Id` fallback。
- Bearer token 无效时直接 401，不 fallback demo header。
- 移动端支持 `mock`、`api-demo`、`api-auth`。
- 移动端设置页显示 auth mode、用户摘要和 token 短摘要。

## 未完成能力

- OAuth。
- 短信验证码。
- 邮箱验证。
- 找回密码。
- 设备管理。
- 管理员后台。
- Native SecureStore 持久化。
- 生产级登录风控。

## 安全边界

- JWT 不绕过 family permissions。
- Agent API 不绕过 Runtime、Safety Policy 或 Tool Executor。
- LLM 仍只在 `daily_health_brief` 中可选启用。
- 移动端不开放通用 tool execution。
- `.env`、真实 API key、真实 JWT secret、完整 token 不提交。

## 后续建议

下一阶段可以进入文件上传 / OCR / 文档处理增强，或先做 Auth 生产化 review。若进入生产或外部试用，必须先关闭 demo header 并接入安全存储。
