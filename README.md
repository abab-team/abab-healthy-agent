# Family Health Agent

Family Health Agent 是面向家庭长期使用的健康档案、家庭健康共享与受控 Agent 辅助系统。项目当前进入 **Phase 10.A：LLM Client 最小封装**：后端核心业务 API、权限闭环、API 安全、Agent Harness、Agent Tool Executor、受控 Agent workflow、Agent API 最小入口、移动端 MVP 演示闭环已经可验证运行，LLM 底座已开始建设。

本项目不是医疗诊断系统。系统只做生活健康管理、资料整理、趋势提醒和就医沟通辅助，不输出医学诊断、处方建议、药物剂量建议、停药/换药建议，也不把“系统内无记录”表达成“现实没有问题”。

## 当前阶段

当前状态：

- Phase 00-09 已完成。
- Phase 10.A 已新增 LLM Client 最小封装：默认 mock provider、默认 `LLM_ENABLED=false`，并预留 openai-compatible provider。
- Phase 08 已完成 Agent Tool 权限收口、Agent API 最小入口、受控草稿 workflow、受控提醒 workflow。
- Phase 09 已完成移动端 MVP：Expo + React Native App 支持 mock/api mode、只读 demo 数据、`daily_health_brief`、3 个受控写入 workflow、Agent Run 详情和开发者调试状态。
- 当前不是完整产品，仍缺少真实 Auth/JWT、业务 workflow LLM 接入、LangGraph、OCR/upload/RAG、正式上传、生产部署和完整真机视觉 QA。
- 当前阶段为 **Phase 10.A：LLM Client 最小封装**。LLM Client 尚未接入 `daily_health_brief` 或其他 Agent workflow。

## 已具备能力

后端当前已有：

- 数据模型、Alembic migration、demo seed 与 verify 脚本。
- identity、family、permissions、health_profile、health_data、health_record、medical_timeline、document、reports、alerts、audit 等模块化业务基础。
- 普通业务 API 与 family member API。
- 家庭权限闭环、data access logs、统一错误响应。
- API 输入校验、敏感字段拦截、file_path 安全校验与响应脱敏。
- Agent Runtime、Safety Policy、Tool Registry、Tool Executor。
- agent_traces、agent_safety_checks、agent_tool_calls 记录与查询。
- 只读健康 Agent tools 与写入类 draft Agent tools。
- 4 个受控 Agent workflow：
  - `daily_health_brief`
  - `symptom_draft_create`
  - `medical_event_draft_create`
  - `alert_create`
- Agent API：
  - `POST /api/v1/agent/runs`
  - `GET /api/v1/agent/runs/{trace_id}`
  - `GET /api/v1/agent/runs/{trace_id}/tool-calls`
  - `GET /api/v1/agent/runs/{trace_id}/safety-checks`
- LLM Client 最小底座：
  - `mock` provider，默认不请求外部网络。
  - `openai_compatible` provider，读取 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`。
  - 默认 `LLM_ENABLED=false`，当前未接入业务 workflow。

## 未完成能力

当前尚未完成：

- 正式 Web 前端。
- 移动端完整真实 API 联调与发布。
- 真实 Auth/JWT 登录体系。
- 业务 workflow 的 LLM 接入。
- LangGraph workflow。
- OCR / upload / RAG。
- 生产部署、真实通知、真实设备接入。
- 通用 tool execution API。当前刻意不开放任意 `tool_name` / `input_data` 执行。

## 移动端 API 接入状态

`apps/mobile` 当前支持两种数据模式：

- `EXPO_PUBLIC_DATA_MODE=mock`：默认模式，全部使用本地 mock。
- `EXPO_PUBLIC_DATA_MODE=api`：接入只读 demo 数据、`GET /health`、`daily_health_brief` 与 3 个受控写入类 workflow。

手机真机访问电脑上的 FastAPI 不能使用 `localhost` 或 `127.0.0.1`，需要配置电脑局域网 IP，例如 `http://192.168.x.x:8000`。当前仍使用开发调试 header `X-Current-User-Id`，不是正式 Auth/JWT。

写入类 workflow（`symptom_draft_create`、`medical_event_draft_create`、`alert_create`）在移动端 `api` mode 下已连接真实 Agent API，但仍只通过固定 workflow 调用，不开放通用 tool execution，不允许页面传 `tool_name` 或 `input_data`。

Phase 09.3.B 已补充移动端与后端 smoke runbook，并在本机通过临时 SQLite smoke DB 验证 `/health`、`daily_health_brief`、Agent run / tool_calls / safety_checks 查询。详见 `docs/frontend/MOBILE_BACKEND_SMOKE_RUNBOOK.md`。

Phase 09.3.C 已补充移动端只读 API 模式的 loading/error/empty 状态和 API/mock/待接入标识，并新增真机 QA 清单：`docs/frontend/MOBILE_DEVICE_QA_CHECKLIST.md`。

Phase 09.3.D 已补充写入类 workflow 的 preview / confirm 接入：

- `symptom_draft_create`：预览不写入，确认后创建待确认症状草稿。
- `medical_event_draft_create`：预览不写入，确认后创建待确认健康事件草稿。
- `alert_create`：预览不写入，确认后创建普通健康提醒。

草稿列表和正式确认入库仍未真实接入，后续 Phase 再处理。

Phase 09.3.E 已补充：

- 写入页面的 mock/api、preview/confirm、loading、success、error 与安全阻断状态展示。
- 写入成功后的 trace_id 摘要与 Agent Run 详情入口。
- Agent Run 详情的安全摘要展示。
- 写入 workflow QA 清单：`docs/frontend/WRITE_WORKFLOW_QA_CHECKLIST.md`。

## 重要说明

当前不是“产品只有 4 个功能”。当前只是 **Agent API 对外开放了 4 个受控 workflow**。产品功能、普通 API、Agent Tool、Agent Workflow、前端页面是不同层级，后续会分别按功能覆盖矩阵推进。

功能覆盖与后续 Phase 映射请阅读：

- `docs/architecture/FEATURE_COVERAGE_MATRIX.md`
- `docs/frontend/FRONTEND_MVP_SCOPE.md`
- `docs/frontend/MOBILE_MVP_DEMO_SCRIPT.md`
- `docs/frontend/MOBILE_MVP_ACCEPTANCE_CHECKLIST.md`
- `docs/frontend/PHASE_09_FINAL_REVIEW.md`
- `docs/architecture/PHASE_PROGRESS.md`
- `docs/architecture/PHASE_08_SCOPE_RECONCILIATION.md`

## 架构原则

- Monorepo。
- 模块化单体后端。
- 多前端入口预留。
- Agent Core 独立于业务模块。
- 业务事实放在 `backend/app/modules/`。
- Agent 不直接访问数据库，只能通过受控 Tool 调用业务 service。
- 家人数据访问必须经过 `family_id` 与权限检查。
- 写入类 Agent Tool 必须经过 confirmation。
- 未确认草稿不能成为正式健康事实。

## 目录结构

```text
family-health-agent/
|-- apps/
|-- backend/
|-- packages/
|-- infra/
|-- docs/
|-- prompts/
|-- datasets/
|-- tools/
|-- docker-compose.yml
|-- docker-compose.dev.yml
|-- .env.example
|-- README.md
`-- Makefile
```

后端核心结构：

```text
backend/
|-- app/
|   |-- core/
|   |-- db/
|   |-- api/
|   |-- modules/
|   |-- agent/
|   |-- integrations/
|   |-- jobs/
|   |-- workers/
|   |-- common/
|   `-- utils/
|-- alembic/
|-- tests/
|-- scripts/
`-- storage/
```

## 调整后的阶段顺序

原始阶段计划仍保留在 `CODEX_IMPLEMENTATION_PLAN.md`。基于当前实际进度，Phase 08 后的执行顺序调整为：

```text
Phase 09: 可用前端 / 调试页面
Phase 10: LLM Client 最小封装
Phase 11: LLM 安全增强 Agent 输出
Phase 12: LangGraph Workflows
Phase 13: 文件上传 / OCR / 文档处理增强
Phase 14: RAG / 健康知识库
Phase 15: 真实 Auth / 部署 / 产品化收口
```

Phase 09 优先做可用前端 / 调试页面，是为了更快验证已有普通 API、Agent API、权限、草稿确认、trace/tool_calls/safety_checks 的产品闭环。LLM 与 LangGraph 后移，避免在没有可操作界面的情况下继续堆叠不可见能力。

## LLM Client 状态

Phase 10.A 只完成 LLM Client 底座，不改变现有 Agent workflow 行为：

- 默认 `LLM_ENABLED=false`。
- 默认 `LLM_PROVIDER=mock`。
- `mock` provider 返回稳定文本，适合测试和本地开发。
- `openai_compatible` provider 只在显式启用且配置 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL` 后才会请求外部服务。
- LLM Client 不查数据库、不调用 tool、不写业务数据。
- 后续任何 LLM 输出接入 Agent workflow 前，都必须经过 Safety Policy。

## 本地命令

常用 Makefile 命令：

```text
make help
make dev
make backend-dev
make test
make lint
make format
make migrate
make seed
make verify-demo
```

任何开发任务开始前必须先阅读 `AGENTS.md`、`CODEX_IMPLEMENTATION_PLAN.md` 与相关架构文档，并严格遵守当前 Phase 范围。
