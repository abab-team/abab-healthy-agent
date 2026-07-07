# Auth QA Checklist

Phase 12 移动端 Auth/JWT 验收清单。

## Mock Mode

- [ ] `EXPO_PUBLIC_DATA_MODE=mock` 时不请求后端。
- [ ] 登录页可打开，但核心页面仍使用 mock 数据。
- [ ] 设置页明确显示当前为 mock / demo 状态。

## API Demo Mode

- [ ] `EXPO_PUBLIC_AUTH_MODE=demo` 时请求携带 `X-Current-User-Id`。
- [ ] `/health` 可刷新。
- [ ] `daily_health_brief` 可执行。
- [ ] 3 个写入 workflow preview/confirm 仍通过固定 workflow。
- [ ] 不允许 `tool_name` / `input_data`。

## API Auth Mode

- [ ] `EXPO_PUBLIC_AUTH_MODE=auth` 时不发送 demo header。
- [ ] 登录页可使用 demo 邮箱/密码登录。
- [ ] 登录失败显示错误，不泄露密码/token。
- [ ] 登录成功后设置页显示当前用户摘要。
- [ ] 设置页只显示 token 短摘要，不显示完整 token。
- [ ] API 请求携带 `Authorization: Bearer`。
- [ ] 401 时会尝试 refresh。
- [ ] refresh 失败后清理 session。
- [ ] 退出登录后 refresh token 不再可用。

## Agent API

- [ ] `daily_health_brief` 在 auth mode 下可运行。
- [ ] Agent Run 详情可查询 trace/tool_calls/safety_checks。
- [ ] 权限不足时不泄露目标数据。
- [ ] Agent Safety / Tool Executor 未被绕过。

## 真机

- [ ] 真机使用电脑局域网 IP，不使用 localhost。
- [ ] 手机和电脑在同一 Wi-Fi。
- [ ] 如扫码失败，可尝试 tunnel。
- [ ] 不同屏幕下 token 短摘要不会撑爆布局。

## 安全边界

- [ ] UI 不出现完整 access token。
- [ ] UI 不出现完整 refresh token。
- [ ] console 不输出 token。
- [ ] 不展示 password、secret、api_key。
- [ ] 不实现 OAuth、短信验证码、邮箱验证或找回密码。
