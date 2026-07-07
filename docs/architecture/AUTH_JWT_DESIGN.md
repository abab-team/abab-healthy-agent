# Auth / JWT Design

本文档记录 Phase 12 的 Auth/JWT 与用户会话基础。

## 目标

Phase 12.A 建立后端登录会话底座：

- password hash
- access token
- refresh token
- logout
- `/api/v1/auth/me`
- auth smoke tests

Phase 12.B 起，后端统一 current user dependency 已支持 JWT；Phase 12.C 起，移动端可在 `api-auth` 模式下使用 Bearer token。开发期 `X-Current-User-Id` fallback 仍保留，但只能在 `AUTH_DEMO_HEADER_ENABLED=true` 时使用。

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
AUTH_DEMO_HEADER_ENABLED=true
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
```

`JWT_SECRET_KEY` 必须来自本地 `.env` 或部署环境变量。`.env.example` 中的值只是占位，不能用于生产。

## Current User 解析顺序

Phase 12.B 后，普通业务 API 与 Agent API 通过统一依赖识别当前用户：

1. 如果存在 `Authorization: Bearer <access_token>`，优先使用 JWT。
2. 如果 Bearer token 无效，直接返回 401，不回退 demo header。
3. 如果没有 Bearer token，且 `AUTH_DEMO_HEADER_ENABLED=true`，允许 `X-Current-User-Id`。
4. 如果没有可用身份，返回 401。

JWT 只负责识别 `current_user_id`。家庭共享权限仍由 family / permissions 服务判断，Agent API 仍必须经过 Runtime、Safety Policy 与 Tool Executor。

## 移动端模式

Phase 12.C 后移动端支持：

- `EXPO_PUBLIC_DATA_MODE=mock`：纯 mock，不请求后端。
- `EXPO_PUBLIC_DATA_MODE=api` + `EXPO_PUBLIC_AUTH_MODE=demo`：发送 `X-Current-User-Id`。
- `EXPO_PUBLIC_DATA_MODE=api` + `EXPO_PUBLIC_AUTH_MODE=auth`：发送 `Authorization: Bearer`。

当前移动端 Web 环境使用 `localStorage` 保存 session；Native 环境暂使用内存 fallback。生产发布前应接入 Expo SecureStore 或等价安全存储。

## Phase 12 边界

- 不实现 OAuth。
- 不实现短信验证码。
- 不实现邮箱验证。
- 不实现找回密码。
- 不修改 Agent workflow。
- 不修改 LLM 行为。
- 不删除 demo header fallback，但生产环境必须禁用。

## 后续事项

- 生产前必须设置强 `JWT_SECRET_KEY`。
- 生产前必须设置 `AUTH_DEMO_HEADER_ENABLED=false`。
- 移动端 Native 持久化需要 SecureStore。
- 仍未实现 OAuth、短信验证码、邮箱验证、找回密码、设备管理和管理员 RBAC。
