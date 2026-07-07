# Auth Security Notes

本文档记录 Phase 12.D 的 Auth/JWT 安全收口。

## 已完成

- 密码使用 PBKDF2-SHA256 哈希保存，不保存明文。
- access token 使用 HMAC-SHA256 JWT，包含 `sub`、`sid`、`typ`、`iat`、`exp`。
- refresh token 使用随机 opaque token，数据库只保存 SHA-256 hash。
- refresh 会轮换 refresh token，旧 refresh token 立即失效。
- logout 会 revoke refresh token。
- Bearer token 优先于 demo header；无效 Bearer token 不会 fallback 到 demo header。
- `AUTH_DEMO_HEADER_ENABLED=false` 时，`X-Current-User-Id` 不再被接受。
- API 错误响应不回显密码、token、secret 或原始异常。
- 移动端设置页只显示 access token 短摘要，不展示完整 token。

## 生产前必须确认

- `JWT_SECRET_KEY` 必须是强随机值，不能使用 `.env.example` 占位。
- `AUTH_DEMO_HEADER_ENABLED=false`。
- `AUTH_DEMO_LOGIN_ENABLED` 是否继续开启必须经产品/安全 review。
- 移动端 Native 存储应接入 SecureStore 或等价安全存储。
- 登录失败次数限制、设备管理、密码重置、邮箱/短信验证尚未实现。

## 保持不变的边界

- JWT 只识别当前用户，不替代 family / permissions 权限判断。
- Agent API 仍使用受控 workflow，不开放通用 tool execution。
- Agent 输出仍必须经过 Safety Policy。
- LLM 仍只在 `daily_health_brief` 中可选启用。
