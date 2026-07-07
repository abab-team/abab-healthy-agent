# Auth / JWT Design

本文档记录 Phase 12.A 的最小 Auth/JWT 与用户会话基础。

## 目标

Phase 12.A 只建立后端登录会话底座：

- password hash
- access token
- refresh token
- logout
- `/api/v1/auth/me`
- auth smoke tests

本阶段不替换现有 `X-Current-User-Id` demo header，也不强制所有 API 立刻使用 JWT。JWT current user dependency 的迁移放在 Phase 12.B。

## 复用的数据表

Phase 12.A 复用 Phase 02 已存在的表：

- `users`
- `login_sessions`
- `refresh_tokens`

因此本阶段不新增 migration，不新增数据库模型。

## Token 策略

- access token 是 HMAC-SHA256 JWT，包含 `sub`、`sid`、`typ=access`、`iat`、`exp`。
- refresh token 是随机 opaque token，只保存 SHA-256 hash。
- logout 会 revoke refresh token。
- refresh 会 rotate refresh token，旧 refresh token 立即失效。
- token 不写入日志，不进入错误响应，不在文档中展示真实值。

## 密码策略

- 使用 PBKDF2-SHA256 保存密码哈希。
- 不保存明文密码。
- 登录失败使用统一 401，不泄露邮箱是否存在或密码是否错误。

## 配置

默认配置：

```text
AUTH_ENABLED=false
AUTH_DEMO_LOGIN_ENABLED=true
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
```

`JWT_SECRET_KEY` 必须来自本地 `.env` 或部署环境变量。`.env.example` 中的值只是占位，不能用于生产。

## Phase 12.A 边界

- 不实现 OAuth。
- 不实现短信验证码。
- 不实现邮箱验证。
- 不实现找回密码。
- 不修改移动端。
- 不修改 Agent workflow。
- 不修改 LLM 行为。
- 不删除 demo header fallback。
- 不强制所有 API 立刻 JWT。

## 后续 Phase 12.B

Phase 12.B 将新增统一 current user dependency，按以下优先级解析：

1. `Authorization: Bearer <access_token>`
2. `AUTH_DEMO_HEADER_ENABLED=true` 时允许 `X-Current-User-Id`
3. 否则返回 401

家庭权限、Agent Safety、Tool Executor 仍必须保持独立生效，不能被 JWT 绕过。
