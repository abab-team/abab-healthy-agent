# API Contract Checklist

本文档用于 Phase 09.3 正式接入 FastAPI 的契约核对。Phase 09.3.A 已完成 API Client 基础接入，但只开放只读 demo 数据与 `daily_health_brief`。

## Phase 09.3.A 已对齐

- API base URL 通过 `EXPO_PUBLIC_API_BASE_URL` 注入，无硬编码 localhost 默认值。
- 数据模式通过 `EXPO_PUBLIC_DATA_MODE=mock/api` 切换，默认 mock。
- API mode 使用 `X-Current-User-Id` demo header。
- `AgentRunRequest.workflow_type` 仍为受控 union，不允许任意 string。
- `tool_name` / `input_data` 仍为 `never`，前端不开放通用 tool execution。
- `POST /api/v1/agent/runs` 当前仅在 provider 中用于 `daily_health_brief`。
- Agent Run 详情只展示 trace、tool_calls、safety_checks 安全摘要。

## Phase 09.3.A 未对齐 / 后续处理

- 写入类 workflow：`symptom_draft_create`、`medical_event_draft_create`、`alert_create` 仍为 mock。
- 草稿确认、修改、暂不处理仍为本地状态。
- 首页今日待办、最近动态仍使用 mock 聚合。
- 家庭权限概览仍是静态摘要，后续需要前端 view model。
- 后端 demo user UUID 需要由 seed 后的真实数据或环境变量提供，前端不自行猜测身份。

## 接入前必须确认

- API base URL 是否使用局域网 IP，而不是手机上的 `localhost`。
- 是否仍使用 `X-Current-User-Id` demo header，并明确标注开发调试模式。
- 每个请求是否显式传入 `target_user_id`。
- family 场景是否显式传入 `family_id`。
- 前端是否没有自行猜测 `current_user_id`、`family_id`、`target_user_id`。
- 前端是否没有开放 `tool_name` / `input_data`。

## 页面所需接口

| 页面 | 需要确认的接口 |
| --- | --- |
| 首页 | 当前用户、家庭概览、待办、最近动态、Agent 简报入口 |
| 家庭 | 家庭成员、成员详情、共享权限概览 |
| 草稿 | 草稿列表、草稿状态更新、草稿确认 |
| 创建症状草稿 | `POST /api/v1/agent/runs` with `symptom_draft_create` |
| 创建健康事件草稿 | `POST /api/v1/agent/runs` with `medical_event_draft_create` |
| 创建提醒 | `POST /api/v1/agent/runs` with `alert_create` |
| 今日健康简报 | `POST /api/v1/agent/runs` with `daily_health_brief` |
| Agent Run 详情 | trace、tool_calls、safety_checks 查询 |

Phase 09.3.A 中，只有今日健康简报实际请求 Agent API；草稿和提醒写入仍等待后续 Phase。

## Phase 09.3.B Smoke Checklist

已验证：

- 后端依赖可通过 Codex bundled Python + 临时 `.venv-smoke` 安装。
- SQLite smoke DB 可运行 Alembic migration 到 head。
- `seed_demo_data.py` 与 `verify_demo_data.py` 可在 smoke DB 上通过。
- `GET /health` 返回 200。
- `POST /api/v1/agent/runs` with `workflow_type=daily_health_brief` 返回 `completed`。
- Agent run detail / tool-calls / safety-checks 查询可用。
- 移动端 `EXPO_PUBLIC_DATA_MODE=api` Web dev server 可启动。

环境说明：

- 系统 Python `pip` 当前损坏，错误为 `No module named 'pip._vendor.rich.console'`。
- Docker Desktop engine 当前未运行，PostgreSQL compose 路径未完成。
- PostgreSQL 正式联调仍建议按 runbook 启动 Docker Desktop 后执行。

仍禁止：

- `symptom_draft_create` 真实调用。
- `medical_event_draft_create` 真实调用。
- `alert_create` 真实调用。
- 通用 `tool_name` / `input_data`。

## Phase 09.3.C UI Contract

- API mode 必须显示 loading / error / empty 状态。
- 后端不可用时必须显示可理解的错误提示。
- mock 数据、真实 API 数据、fallback 数据、待接入区域必须有明确标识。
- 设置页必须显示 data mode、API Base URL、`X-Current-User-Id` 与 `/health` 状态。
- 写入类页面仍为 mock，不触发真实后端 workflow。
- 真机 QA 步骤记录在 `docs/frontend/MOBILE_DEVICE_QA_CHECKLIST.md`。

## Agent Run Request

必须支持：

- `target_user_id`
- `family_id`
- `workflow_type`
- `user_message`
- `confirmation`
- `workflow_payload`
- `source`

必须拒绝：

- `tool_name`
- `input_data`

## 错误处理策略

- 使用后端统一错误格式。
- validation error 只展示字段级摘要。
- 403/404 不泄露其他用户或家庭数据存在性。
- 500 不展示 traceback、SQL、本机路径或原始异常细节。

## 脱敏要求

前端 response 展示必须继续隐藏：

- 健康原文长文本
- 文件路径
- 文档抽取全文
- token / password / api key
- traceback / SQL

## 安全文案

前端必须持续强调：

- 根据系统内记录。
- 草稿需要确认。
- 普通健康提醒不是急救。
- 内容不替代医生建议。

## Phase 09.3.D 写入类 Workflow 契约

Phase 09.3.D 已接入以下受控 workflow：

- `symptom_draft_create`
- `medical_event_draft_create`
- `alert_create`

契约要求：

- 所有调用必须走 `POST /api/v1/agent/runs`。
- `preview` 必须使用 `confirmation=false`，不得显示为已写入。
- `confirm` 必须使用 `confirmation=true`。
- `symptom_draft_create` confirm 后只创建待确认症状草稿。
- `medical_event_draft_create` confirm 后只创建待确认健康事件草稿。
- `alert_create` confirm 后只创建普通健康提醒。
- 页面不得传 `tool_name` 或 `input_data`。
- 前端不得开放通用 tool execution。
- 错误必须显示为权限、safety、网络或后端错误，不得静默 fallback 成真实成功。
- Agent Run 详情继续只展示 trace、tool_calls、safety_checks 安全摘要。

仍未接入：

- 草稿列表真实查询。
- 草稿正式确认入库。
- 真实 Auth/JWT。
- LLM、LangGraph、OCR/upload/RAG。

## Phase 09.3.E 验收补充

- 写入 workflow UI 只基于 Phase 09.3.D 已有 API 契约打磨。
- 不新增后端 API。
- 不开放任意 workflow 或 tool execution。
- `tool_name` / `input_data` 继续禁止。
- API mode 失败不得自动 fallback mock。
- 真机 QA 仍需用户手动完成，步骤见 `docs/frontend/WRITE_WORKFLOW_QA_CHECKLIST.md`。

## Phase 09.4 Final Review 补充

- Phase 09.4 没有新增后端 API。
- 移动端仍只调用受控 API，不开放通用 tool execution。
- `daily_health_brief`、`symptom_draft_create`、`medical_event_draft_create`、`alert_create` 仍是唯一开放的 Agent workflow 集合。
- MVP 演示与验收入口见 `MOBILE_MVP_DEMO_SCRIPT.md`、`MOBILE_MVP_ACCEPTANCE_CHECKLIST.md` 和 `PHASE_09_FINAL_REVIEW.md`。

## Phase 12 Auth Contract

Phase 12 新增认证契约：

- `EXPO_PUBLIC_AUTH_MODE=demo`：继续使用 `X-Current-User-Id`。
- `EXPO_PUBLIC_AUTH_MODE=auth`：使用 `Authorization: Bearer`。
- 登录页只调用 `POST /api/v1/auth/login`。
- refresh 只调用 `POST /api/v1/auth/refresh`。
- logout 只调用 `POST /api/v1/auth/logout`。
- 设置页只展示 token 短摘要。

必须继续确认：

- API client 不在 console 输出完整 token。
- UI 不展示完整 access token 或 refresh token。
- auth mode 下不发送 demo header。
- demo header fallback 只用于开发。
- JWT 用户仍不能绕过 family permissions。
- Agent API 仍不能绕过 Safety Policy / Tool Executor。
## Phase 14 RAG API Contract

Phase 14 新增后端受控 RAG API，但移动端暂未接入 RAG 页面。

新增接口：

- `POST /api/v1/rag/search`

契约：

- 使用当前登录用户或 demo header 用户作为 `current_user_id`。
- 可传 `target_user_id`、`family_id`、`query`、`source_types`、`top_k`。
- family 访问必须继续走权限系统。
- response 只返回 safe excerpt、citation、source metadata。
- response 不返回 `raw_text`、`symptom_text`、`raw_extracted_text`、`file_path`、token、password、API key、traceback、SQL。
- 该接口不生成医学回答，不开放通用 tool execution。
