# Family Health Agent Mobile

这是 family-health-agent 的 React Native + Expo 移动端 MVP。Phase 09.4 已完成移动端 MVP 收口，用于演示家庭概览、成员详情、AI 健康简报、受控写入类 Agent workflow、Agent Run 安全摘要和开发者调试状态。

默认版本仍使用本地 mock 数据。只有在显式设置 `EXPO_PUBLIC_DATA_MODE=api` 后，才会请求 FastAPI。

Phase 12 已接入最小 Auth/JWT 登录态。当前仍不实现 OAuth、短信验证码、邮箱验证、LangGraph、OCR、RAG、上传或推送通知。

## 页面范围

- 首页：家庭今日概览、今日待办、AI 今日简报、快速记录、最近动态。
- 家庭：家庭卡片、成员列表、共享权限概览、邀请成员入口。
- AI 管家：安全提示、推荐动作、待确认草稿、AI 执行记录、Trace 调试摘要。
- 设置：用户卡片、个人资料、通知、家庭共享、隐私、数据来源、开发者调试、关于 App。

二级静态页面：

- `/member/[id]`
- `/drafts`
- `/agent-brief`
- `/create-symptom-draft`
- `/create-health-event-draft`
- `/create-alert`
- `/agent-run/[id]`

## 本地运行

```bash
npm install
npm run web
```

也可以直接运行：

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
- `EXPO_PUBLIC_DATA_MODE=api`：请求 FastAPI，接入只读 demo API、`GET /health`、`daily_health_brief` 与受控写入类 Agent workflow。
- `EXPO_PUBLIC_AUTH_MODE=demo`：api mode 下发送 `X-Current-User-Id`，用于开发调试。
- `EXPO_PUBLIC_AUTH_MODE=auth`：api mode 下使用登录页、Bearer token、refresh 和 logout。
- `EXPO_PUBLIC_API_BASE_URL`：FastAPI 地址，例如 Web 本机调试可用 `http://localhost:8000`。
- `EXPO_PUBLIC_DEMO_USER_ID`：api-demo 调试用户 ID，会作为 `X-Current-User-Id` header 发送。

手机真机访问电脑后端时不能使用 `localhost` 或 `127.0.0.1`，需要使用电脑局域网 IP，例如：

```text
http://192.168.x.x:8000
```

## Phase 09.4 API 范围

已接入：

- `GET /health`
- `GET /api/v1/families`
- `GET /api/v1/families/{family_id}/members`
- 部分家庭成员健康档案、血压、症状摘要、提醒只读接口
- `POST /api/v1/agent/runs`，用于 `daily_health_brief`、`symptom_draft_create`、`medical_event_draft_create`、`alert_create`
- Agent run / tool-calls / safety-checks 安全摘要查询

仍保持 mock：

- 草稿确认、修改、暂不处理
- 今日待办、最近动态等聚合数据

移动端不会开放通用 tool execution，不允许用户直接传 `tool_name` 或 `input_data`。写入类页面只暴露固定 preview / confirm 方法：

- `symptom_draft_create`：`confirmation=false` 只做预览，`confirmation=true` 创建待确认症状草稿。
- `medical_event_draft_create`：`confirmation=false` 只做预览，`confirmation=true` 创建待确认健康事件草稿。
- `alert_create`：`confirmation=false` 只做预览，`confirmation=true` 创建普通健康提醒。

## Phase 09.3.B Smoke 结果

Phase 09.3.B 已补充前后端联调 runbook：`docs/frontend/MOBILE_BACKEND_SMOKE_RUNBOOK.md`。

本机验证结论：

- 系统 Python 3.11 的 `pip` 损坏，无法直接安装后端依赖。
- Docker CLI 可用，但 Docker Desktop engine 未运行，因此无法启动 PostgreSQL 容器。
- 使用 Codex bundled Python 创建临时 `.venv-smoke`，并用临时 SQLite smoke DB 完成后端 smoke。
- `GET /health` 返回 200。
- `daily_health_brief` 返回 `completed`，可查询 5 条 tool calls 与 2 条 safety checks。
- 移动端 `api` mode Web 预览可启动并返回 HTTP 200。

Phase 09.3.D 新增写入类 workflow smoke 脚本：`scripts/smoke/mobile_write_workflows_smoke.ps1`。该脚本只用于本地 demo DB 验证，会创建测试草稿和普通提醒数据，不应连接生产数据。

## Phase 09.3.C 体验打磨

Phase 09.3.C 补充了只读 API 模式的 loading / error / empty 状态，以及 API / mock / 待接入标识。

重点说明：

- 首页、家庭、成员详情、AI 管家、Agent Run 详情会明确标注数据来源。
- 设置页开发者调试区展示 data mode、API Base URL、`X-Current-User-Id`、`/health` 状态和真机访问提示。
- 写入类 workflow 已在 `api` mode 下接入受控 Agent API；`mock` mode 仍只做静态预览，不会真实提交。
- 真机 Expo Go 手动 QA 请按 `docs/frontend/MOBILE_DEVICE_QA_CHECKLIST.md` 执行。

## Phase 09.3.D 受控写入说明

- 写入页面在 `mock` mode 下显示静态预览，不请求后端。
- 写入页面在 `api` mode 下只通过 `POST /api/v1/agent/runs` 调用固定 workflow。
- 预览按钮使用 `confirmation=false`，不会写入。
- 确认按钮使用 `confirmation=true`，只创建待确认草稿或普通健康提醒。
- 草稿列表页仍为 mock，真实草稿列表和正式确认入库留到后续阶段。
- 当前已接入最小 Auth/JWT；仍不实现 OAuth/短信/邮箱验证，不调用写入类 LLM，不实现 LangGraph/OCR/upload/RAG。

## Phase 09.3.E 写入流程体验收口

Phase 09.3.E 只做移动端 UI 与 QA 文档打磨，不新增后端能力：

- 写入页面统一显示 mock/api、preview/confirm、loading、success、error 和 safety blocked 状态。
- 写入成功后显示 trace_id 摘要，并可跳转 Agent Run 详情。
- Agent Run 详情继续只展示安全摘要。
- 草稿列表仍为 mock，真实草稿列表和正式确认入库后续实现。
- 写入 workflow QA 清单见 `docs/frontend/WRITE_WORKFLOW_QA_CHECKLIST.md`。

## Phase 12 Auth/JWT

Phase 12.C 后移动端支持最小登录态：

- `/login` 登录页。
- api-auth mode 自动发送 `Authorization: Bearer`。
- access token 过期时尝试 refresh。
- refresh 失败后清理 session。
- 设置页提供 logout，并只展示 token 短摘要。
- api-demo mode 和 mock mode 仍保留。

本阶段没有实现 OAuth、短信验证码、邮箱验证、找回密码或完整账号中心。Native 环境当前未接入 SecureStore，生产发布前需要补安全存储。

详见：

- `docs/frontend/AUTH_MOBILE_RUNBOOK.md`
- `docs/frontend/AUTH_QA_CHECKLIST.md`

## Phase 09.4 MVP 收口

Phase 09.4 不新增后端能力，只做移动端 MVP 闭环、文档和最终验收：

- 首页、家庭页、成员详情、AI 管家、写入 workflow、Agent Run 详情、草稿页和设置页完成演示路径收口。
- 新增 `docs/frontend/MOBILE_MVP_DEMO_SCRIPT.md`，用于本地 Web 与 Expo Go 演示。
- 新增 `docs/frontend/MOBILE_MVP_ACCEPTANCE_CHECKLIST.md`，用于页面、API、写入 workflow、安全文案和真机 QA 验收。
- 新增 `docs/frontend/PHASE_09_FINAL_REVIEW.md`，记录 Phase 09 完成范围、验证结果和剩余风险。
- 草稿列表仍为 mock，正式确认入库后续实现。

## Expo Go 预览

```bash
npm start
```

然后用手机上的 Expo Go 扫描终端或浏览器中的二维码。

## 安全边界

移动端文案必须保持“根据系统内记录”“不替代医生诊断或治疗建议”“普通提醒不是急救服务”。当前只接入最小 Auth/JWT，不实现 OAuth/短信/邮箱验证，不实现 LangGraph，不实现 OCR/upload/RAG。

## Phase 15 真机演示说明

Phase 15 的移动端目标是可演示 MVP，而不是生产发布包。

推荐演示模式：

```text
EXPO_PUBLIC_DATA_MODE=api-auth
EXPO_PUBLIC_API_BASE_URL=http://<电脑局域网IP>:8000
```

注意：

- Expo Go 真机不能使用 `localhost` 或 `127.0.0.1` 访问电脑后端。
- 手机和电脑需要在同一 Wi-Fi。
- 后端需要以 `--host 0.0.0.0 --port 8000` 启动。
- 防火墙需要允许端口 `8000`。
- 当前仍是 MVP 演示体验，真实生产发布前需要补充 SecureStore、正式隐私策略、生产配置和完整真机 QA。

写入类 workflow 仍然受控：

- preview 不写入。
- confirm 只创建待确认草稿或普通提醒。
- 不开放通用 tool execution。
- 不允许页面传 `tool_name` 或 `input_data`。
- 不提供诊断、处方、剂量或停药建议。
