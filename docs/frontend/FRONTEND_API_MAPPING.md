# Frontend API Mapping

本文档记录 Phase 09 前端与后端 API 的对接计划。Phase 09.3.A 已开始接入前端 API Client，但范围仅限只读 demo 数据与 `daily_health_brief`。

## Phase 09.3.A 状态

- 新增 `apiConfig` / `apiClient` / `backendApi` / `dataProvider`，支持 `mock` 与 `api` 数据模式。
- 默认仍为 `EXPO_PUBLIC_DATA_MODE=mock`。
- `api` 模式需要显式配置 `EXPO_PUBLIC_API_BASE_URL`，不提供硬编码 localhost 默认值。
- 当前仍使用 `X-Current-User-Id` demo header，不是 Auth/JWT。
- 当前只接入只读 family / member / health summary 数据、`GET /health`、`daily_health_brief` 与 Agent run 安全摘要查询。
- 写入类 workflow 仍保持 mock，不请求真实后端。

## Phase 09.2 状态

- 当前移动端仍使用 `apps/mobile/lib/mockApi.ts`。
- 当前移动端新增 `apps/mobile/types/api.ts` 作为 TypeScript API 契约草案。
- 当前不创建真实 API client。
- 当前不调用 `fetch` / `axios` 请求 FastAPI。
- 当前不实现 Auth/JWT。
- 当前不调用 LLM、LangGraph、OCR/upload/RAG。

## Phase 09.3 接入原则

Phase 09.3 才允许把 `mockApi` 替换或包裹为真实 FastAPI 请求。

真机访问本机后端时不能使用 `localhost` 或 `127.0.0.1`，应使用电脑局域网 IP，例如：

```text
http://192.168.x.x:8000
```

当前后端仍使用开发调试身份入口：

```text
X-Current-User-Id: <demo_user_id>
```

该 header 只用于开发调试，不是正式 Auth/JWT。

## 页面到 API 的映射草案

| 页面 | Phase 09.2 mock 方法 | Phase 09.3 预期 API |
| --- | --- | --- |
| 首页 | `getCurrentUser`, `getFamilyOverview`, `getAgentBrief` | identity / family / agent runs |
| 家庭页 | `getFamilyOverview`, `getMemberDetail` | family member APIs |
| 成员详情 | `getMemberDetail` | family member profile / health summary APIs |
| 草稿页 | `getDrafts`, `updateDraftStatus` | Phase 09.3.A 仍为 mock |
| 创建症状草稿 | `createSymptomDraftPreview`, `createSymptomDraftConfirmed` | Phase 09.3.A 仍为 mock |
| 创建健康事件草稿 | mock local state | Phase 09.3.A 仍为 mock |
| 创建提醒 | `createAlertPreview`, `createAlertConfirmed` | Phase 09.3.A 仍为 mock |
| 今日健康简报 | `getAgentBrief` | `POST /api/v1/agent/runs` with `daily_health_brief` |
| Agent Run 详情 | `getAgentRun` | `GET /api/v1/agent/runs/{trace_id}` + tool-calls + safety-checks |

## Phase 09.3.A 已接 API

- `/health`
- `/api/v1/families`
- `/api/v1/families/{family_id}/members`
- `/api/v1/families/{family_id}/permissions`
- `/api/v1/health-profile/me`
- `/api/v1/families/{family_id}/members/{target_user_id}/health-profile`
- `/api/v1/health-data/me/blood-pressure/summary`
- `/api/v1/families/{family_id}/members/{target_user_id}/health-data/blood-pressure/summary`
- `/api/v1/health-records/me/symptoms/summary`
- `/api/v1/families/{family_id}/members/{target_user_id}/health-records/symptoms/summary`
- `/api/v1/families/{family_id}/members/{target_user_id}/alerts/active`
- `/api/v1/agent/runs`，仅 `daily_health_brief`
- `/api/v1/agent/runs/{trace_id}`
- `/api/v1/agent/runs/{trace_id}/tool-calls`
- `/api/v1/agent/runs/{trace_id}/safety-checks`

## Phase 09.3.A 仍为 mock / 后端缺口

- 今日待办与最近动态仍无统一聚合 API。
- 草稿列表与草稿状态更新仍为 mock。
- 写入类 Agent workflow 暂不接真实后端。
- 健康摘要展示仍需要后续统一 response view model。

## Phase 09.3.B Smoke Mapping

本阶段新增 `docs/frontend/MOBILE_BACKEND_SMOKE_RUNBOOK.md`，用于验证 09.3.A 已接入接口。

已完成 smoke：

| 能力 | Smoke 结果 |
| --- | --- |
| `/health` | 200 |
| Alembic migration | 临时 SQLite smoke DB 通过 |
| demo seed / verify | 通过 |
| `daily_health_brief` | `completed` |
| Agent run detail | 可查询 |
| Agent tool_calls | 5 条 |
| Agent safety_checks | 2 条 |
| mobile api mode Web 启动 | HTTP 200 |

未完成 / 待确认：

- Docker PostgreSQL 路径因 Docker Desktop engine 未运行未完成。
- 真机 Expo Go 需要用户按 runbook 配置电脑局域网 IP 后验证。

## Phase 09.3.C Experience Mapping

Phase 09.3.C 不新增后端 API，仅打磨只读 API 前端体验：

| 页面 | 打磨内容 |
| --- | --- |
| 首页 | 家庭成员 API 标识、mock 聚合标识、daily_health_brief loading/success/error/trace |
| 家庭 | API 家庭/成员标识、empty/error 状态、权限概览 mock 标识 |
| 成员详情 | API 摘要标识、mock 补位标识、empty/error 状态 |
| AI 管家 | daily_health_brief 真实 API；写入卡片 mock / 不真实提交 |
| Agent Run | run / tool calls / safety checks 安全摘要、empty/error 状态 |
| 设置 | data mode、API Base URL、demo user id、health 状态、真机局域网提示 |

真机 QA 清单：`docs/frontend/MOBILE_DEVICE_QA_CHECKLIST.md`。

## Agent Workflow Confirmation

Agent API 只允许白名单 workflow：

- `daily_health_brief`
- `symptom_draft_create`
- `medical_event_draft_create`
- `alert_create`

前端交互规则：

- preview：`confirmation=false`
- confirm：`confirmation=true`

前端不得开放：

- `tool_name`
- `input_data`
- 通用 tool execution

## Response 安全要求

前端不得展示：

- `raw_text`
- `file_path`
- `raw_extracted_text`
- token / password / api key
- traceback / SQL
- 过长敏感原文

无记录时应写“系统内暂无相关记录”，不能写成现实身体结论。

## Phase 09.3.D Controlled Write Workflow Mapping

Phase 09.3.D 已在移动端 `api` mode 下接入 3 个写入类 Agent workflow。接入方式仍然是受控 workflow，不是通用 tool execution。

| 页面 | API mode 调用 | preview | confirm | 说明 |
| --- | --- | --- | --- | --- |
| `/create-symptom-draft` | `POST /api/v1/agent/runs` with `symptom_draft_create` | `confirmation=false` | `confirmation=true` | confirm 后只创建待确认症状草稿，不创建正式记录。 |
| `/create-health-event-draft` | `POST /api/v1/agent/runs` with `medical_event_draft_create` | `confirmation=false` | `confirmation=true` | confirm 后只创建待确认健康事件草稿，不创建正式事件。 |
| `/create-alert` | `POST /api/v1/agent/runs` with `alert_create` | `confirmation=false` | `confirmation=true` | confirm 后只创建普通健康提醒，不提供紧急服务。 |

前端仍禁止：

- 页面传入 `tool_name`。
- 页面传入 `input_data`。
- 任意字符串 workflow。
- 直接调用后端业务写入 API。

仍未接入：

- 草稿列表真实查询。
- 草稿正式确认入库。
- 真实 Auth/JWT。
- LLM、LangGraph、OCR/upload/RAG。

## Phase 09.3.E UI Polish

Phase 09.3.E 不新增 API，只打磨现有写入 workflow 的移动端体验：

- 写入页统一展示 mock/api、preview/confirm、loading、success/error、安全阻断状态。
- 写入成功后展示 trace_id 摘要并链接到 Agent Run 详情。
- Agent Run 详情用安全摘要展示 workflow、tool_calls、safety_checks。
- 草稿列表仍为 mock，不实现正式确认入库。

## Phase 09.4 MVP Mapping

Phase 09.4 没有改变 API mapping，只完成移动端 MVP 收口：

- 首页、家庭、成员详情、AI 管家、写入 workflow、Agent Run 详情、草稿页和设置页形成演示路径。
- Web 和 Expo Go 演示方式见 `MOBILE_MVP_DEMO_SCRIPT.md`。
- 页面和 API 验收项见 `MOBILE_MVP_ACCEPTANCE_CHECKLIST.md`。
- 最终结论见 `PHASE_09_FINAL_REVIEW.md`。

## Phase 12 Auth Mapping

Phase 12 后移动端 API client 增加 auth mode，但不改变 Agent workflow 白名单。

数据/认证模式：

- `mock`：`EXPO_PUBLIC_DATA_MODE=mock`，不请求后端。
- `api-demo`：`EXPO_PUBLIC_DATA_MODE=api` + `EXPO_PUBLIC_AUTH_MODE=demo`，发送 `X-Current-User-Id`。
- `api-auth`：`EXPO_PUBLIC_DATA_MODE=api` + `EXPO_PUBLIC_AUTH_MODE=auth`，发送 `Authorization: Bearer`。

新增接口：

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

移动端仍禁止：

- 任意 `workflow_type`。
- `tool_name`。
- `input_data`。
- 通用 tool execution。

Agent API 在 `api-auth` 下仍只允许：

- `daily_health_brief`
- `symptom_draft_create`
- `medical_event_draft_create`
- `alert_create`
## Phase 14 RAG Mapping

当前移动端不直接调用 RAG。Phase 14 后端新增：

| 功能 | API | 移动端状态 | 说明 |
| --- | --- | --- | --- |
| 内部 RAG 搜索 | `POST /api/v1/rag/search` | 未接入 | 仅返回 safe excerpt 与 citation，不生成医学回答 |
| daily_health_brief RAG citation | `POST /api/v1/agent/runs` with `daily_health_brief` | 间接受益 | 仅在 `RAG_ENABLED=true` 时追加 citation，默认关闭 |
| medical_event_draft_create RAG hints | `POST /api/v1/agent/runs` with `medical_event_draft_create` | 间接受益 | 仅在 `RAG_ENABLED=true` 时追加安全 hints，默认关闭 |

移动端后续如接入 RAG citation，仍不得展示 raw text、file_path、raw OCR text、token/password/API key 或医学判断结论。
