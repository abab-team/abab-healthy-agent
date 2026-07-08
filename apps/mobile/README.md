# Family Health Agent Mobile

这是 family-health-agent 的 React Native + Expo 移动端 MVP。当前项目已经完成到 Phase 15：部署 / 真机 QA / 作品集展示收口。

移动端当前用于演示家庭健康管理、家庭共享、受控 Agent workflow、Agent Run 调试摘要，以及与 FastAPI 后端的局域网联调。它仍是 MVP 演示应用，不是生产发布包。

## 当前已具备能力

- `mock` mode：完全使用本地 mock 数据，不请求后端。
- `api` mode：使用 `X-Current-User-Id` demo header 调用 FastAPI。
- `api-auth` mode：支持最小登录态、Bearer token、refresh 与 logout。
- 首页、家庭页、成员详情、AI 管家、设置页、Agent Run 详情页可演示。
- 已接入受控 Agent workflow：
  - `daily_health_brief`
  - `symptom_draft_create`
  - `medical_event_draft_create`
  - `alert_create`
- 写入类 workflow 使用 preview / confirm：
  - preview 不写入。
  - confirm 只创建待确认草稿或普通健康提醒。
- 支持 Agent run / tool_calls / safety_checks 的安全摘要展示。
- 支持文档处理与 OCR preview MVP 入口。
- RAG 当前主要是后端能力和 Agent 内部上下文增强；移动端没有单独 RAG 搜索页面。

## 当前仍未完成

- LangGraph workflow。
- 真实 OCR provider。
- RAG 持久化索引、真实 embedding provider、vector DB。
- 移动端生产发布包。
- 完整真机视觉 QA。
- 草稿正式确认入库的移动端完整闭环。
- OAuth、短信验证码、邮箱验证、找回密码、完整账号中心。
- Native SecureStore 等生产级 token 安全存储。
- 推送通知。

## 页面范围

- 首页：家庭今日概览、今日待办、AI 今日简报、快速记录、最近动态。
- 家庭：家庭卡片、成员列表、共享权限概览、邀请成员入口。
- AI 管家：安全提示、Agent 动作卡片、待确认草稿、AI 执行记录、Trace 调试摘要。
- 设置：用户卡、个人资料、通知、家庭共享、隐私、数据来源、开发者调试、关于 App。

二级页面：

- `/member/[id]`
- `/drafts`
- `/agent-brief`
- `/create-symptom-draft`
- `/create-health-event-draft`
- `/create-alert`
- `/agent-run/[id]`
- `/login`

## 本地运行

```bash
npm install
npm run web
```

也可以运行：

```bash
npx expo start --web
```

## 数据模式与环境变量

复制 `.env.example` 为本地 `.env` 后按需配置：

```text
EXPO_PUBLIC_DATA_MODE=mock
EXPO_PUBLIC_AUTH_MODE=demo
EXPO_PUBLIC_API_BASE_URL=
EXPO_PUBLIC_DEMO_USER_ID=
```

字段说明：

- `EXPO_PUBLIC_DATA_MODE=mock`：默认模式，不请求后端。
- `EXPO_PUBLIC_DATA_MODE=api`：请求 FastAPI，并使用 demo header。
- `EXPO_PUBLIC_DATA_MODE=api-auth`：请求 FastAPI，并使用登录态 Bearer token。
- `EXPO_PUBLIC_AUTH_MODE=demo`：api mode 下发送 `X-Current-User-Id`。
- `EXPO_PUBLIC_AUTH_MODE=auth`：api-auth mode 下使用登录页、Bearer token、refresh 与 logout。
- `EXPO_PUBLIC_API_BASE_URL`：FastAPI 地址。Web 本机调试可用 `http://localhost:8000`。
- `EXPO_PUBLIC_DEMO_USER_ID`：api-demo 调试用户 ID，会作为 `X-Current-User-Id` header 发送。

手机真机访问电脑后端时不能使用 `localhost` 或 `127.0.0.1`，需要使用电脑局域网 IP，例如：

```text
http://192.168.x.x:8000
```

后端需要以 `--host 0.0.0.0 --port 8000` 启动，并确保手机和电脑在同一 Wi-Fi。

## API 范围

移动端当前已接入：

- `GET /health`
- 登录 / refresh / logout / me
- 家庭与成员只读信息
- 部分家庭成员健康档案、血压、症状摘要、提醒只读接口
- `POST /api/v1/agent/runs`
- Agent run / tool-calls / safety-checks 安全摘要查询

`POST /api/v1/agent/runs` 只暴露固定 workflow：

- `daily_health_brief`
- `symptom_draft_create`
- `medical_event_draft_create`
- `alert_create`

移动端不会开放通用 tool execution，不允许页面传 `tool_name` 或 `input_data`。

## 写入 workflow 边界

- `symptom_draft_create`：`confirmation=false` 只做预览，`confirmation=true` 创建待确认症状草稿。
- `medical_event_draft_create`：`confirmation=false` 只做预览，`confirmation=true` 创建待确认健康事件草稿。
- `alert_create`：`confirmation=false` 只做预览，`confirmation=true` 创建普通健康提醒。

仍保持 mock 或后续接入：

- 草稿确认、修改、暂不处理。
- 草稿正式确认入库。
- 正式 symptom_record / medical_event 的移动端确认闭环。
- 今日待办、最近动态等部分聚合数据。

## 文档与 QA

- 后端联调：`docs/frontend/MOBILE_BACKEND_SMOKE_RUNBOOK.md`
- 真机 QA：`docs/frontend/MOBILE_DEVICE_QA_CHECKLIST.md`
- 写入 workflow QA：`docs/frontend/WRITE_WORKFLOW_QA_CHECKLIST.md`
- MVP 演示脚本：`docs/frontend/MOBILE_MVP_DEMO_SCRIPT.md`
- Phase 15 真机 QA：`docs/frontend/MOBILE_REAL_DEVICE_QA.md`

Codex 不能替代真实手机扫码和视觉 QA。Phase 15 后仍需要用户在 Expo Go 真机上完成手动走查、截图或录屏。

## 安全边界

移动端文案必须保持：

- 根据系统内记录。
- 不替代医生诊断或治疗建议。
- 普通健康提醒不是急救服务。
- 如有不适或紧急情况，请联系医生或当地急救服务。

禁止把系统内无记录表达成现实中没有问题。移动端不得输出诊断、处方、剂量、停药建议，也不得暗示自动急救、自动报警、自动联系医院或自动联系家人。
