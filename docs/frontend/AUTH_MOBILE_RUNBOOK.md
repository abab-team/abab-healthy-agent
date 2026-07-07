# Mobile Auth Runbook

本文档用于 Phase 12.C 移动端登录态联调。

## 模式

移动端当前支持三种使用方式：

```text
mock：EXPO_PUBLIC_DATA_MODE=mock
api-demo：EXPO_PUBLIC_DATA_MODE=api + EXPO_PUBLIC_AUTH_MODE=demo
api-auth：EXPO_PUBLIC_DATA_MODE=api + EXPO_PUBLIC_AUTH_MODE=auth
```

## api-demo

```text
EXPO_PUBLIC_DATA_MODE=api
EXPO_PUBLIC_AUTH_MODE=demo
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:18001
EXPO_PUBLIC_DEMO_USER_ID=<seed 后查询到的 Gala user_id>
```

api-demo 会发送 `X-Current-User-Id`。该模式只用于开发调试，不能用于生产。

## api-auth

```text
EXPO_PUBLIC_DATA_MODE=api
EXPO_PUBLIC_AUTH_MODE=auth
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:18001
```

api-auth 会：

- 使用登录页调用 `POST /api/v1/auth/login`。
- 保存 access token / refresh token 会话摘要。
- 普通 API 自动发送 `Authorization: Bearer <access_token>`。
- 401 时尝试 refresh。
- refresh 失败后清理本地 session。
- 设置页只展示 token 短摘要，不展示完整 token。

## Demo 账号

本地 seed 后 demo 用户可以使用：

```text
email: gala.demo@example.com
password: DemoPass123!
```

该密码只用于本地 demo smoke，不是生产初始密码策略。

## 真机注意

Expo Go 真机不能使用 `localhost` 或 `127.0.0.1` 访问电脑后端。请使用电脑局域网 IP：

```text
EXPO_PUBLIC_API_BASE_URL=http://192.168.x.x:8000
```

电脑和手机必须在同一 Wi-Fi；如局域网不可达，可尝试 Expo tunnel。

## Smoke

后端 auth mode smoke：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke/mobile_auth_smoke.ps1 -Python "<codex-bundled-python>"
```

预期：

- login 200
- daily_health_brief 201/completed
- run/tool_calls/safety_checks 查询 200
- `AUTH_DEMO_HEADER_ENABLED=false` 时 demo header 请求 401
