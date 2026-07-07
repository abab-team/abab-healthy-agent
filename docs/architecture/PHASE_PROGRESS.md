# Phase Progress

本文档记录 family-health-agent 的实际实施进度映射。原始阶段计划仍以 `CODEX_IMPLEMENTATION_PLAN.md` 为准；当实际实现与原计划阶段存在重叠时，以本文档说明当前状态与下一步边界。

## Phase 状态表

| Phase | 原计划主题 | 当前状态 | 完成摘要 |
| --- | --- | --- | --- |
| Phase 00 | 仓库与工程规范 | 已完成 | 顶层目录、工程规则、模块边界、README、`.env.example`、Makefile 基础命令已建立。 |
| Phase 01 | 后端基础设施 | 已完成 | FastAPI 最小应用、`/health`、配置、日志、异常基础、SQLAlchemy、Alembic、Docker Compose 基础已完成。 |
| Phase 02 | 数据库模型与 Alembic | 已完成 | identity、family、permissions、health_profile、health_data、health_record、medical_timeline、document、report、alert、agent、audit 等模型与迁移地基已建立。 |
| Phase 03 | Seed Demo Data | 已完成 | deterministic demo 用户、家庭、权限、健康数据、文档、报告、提醒数据与验证脚本已完成。 |
| Phase 04 | 核心业务模块 Service 层 | 已完成 | 主要业务模块 repository / service 已建立，API 与 Agent tools 可复用 service。 |
| Phase 05 | 基础 API 层 | 已完成 | 基础业务 API、family member API、Pydantic schema 与 TestClient 验证已完成。 |
| Phase 06 | 权限系统闭环 | 已完成 | 统一 API 权限守卫、data access logs、统一错误响应、输入校验与安全清洗已通过 Final Review。 |
| Phase 07 | Health Agent Harness | 已完成 | Agent Runtime、Tool Registry、Safety Policy、Tool Executor、只读 tools、draft write tools、`daily_health_brief` workflow 已通过 Final Review。 |
| Phase 08 | Agent Tools | 准备进入 | Phase 07 已提前覆盖部分 Agent Tools 能力；Phase 08 需要做 gap review、补齐缺失 tools 与工具边界收口。 |

## 当前代码实际能力

- 后端模块化单体可以启动，`GET /health` 可用。
- 数据库 migration 可运行到 head。
- demo 数据可 seed 并验证。
- 核心业务模块已具备 service / repository。
- API 已具备基础业务接口、family member 路由、统一权限守卫、统一错误响应和输入安全清洗。
- Agent 层已具备 runtime、trace 生命周期、safety check、tool registry、tool executor、agent_tool_calls 记录。
- Agent 已有第一批只读健康 tools：
  - `health_profile.get`
  - `health_data.blood_pressure.summary`
  - `health_record.symptoms.summary`
  - `medical_timeline.followups.list`
  - `alerts.active.list`
- Agent 已有写入类 draft tools：
  - `health_record.symptom_draft.create`
  - `document_processing.medical_event_draft.create`
  - `alerts.create`
- Agent 已有无 LLM 的 `daily_health_brief` 确定性 workflow。

## 当前未完成能力

- Agent API。
- LLM Client。
- LangGraph workflows。
- RAG / knowledge runtime。
- 真实上传与 OCR 执行链路。
- Web 前端。
- 移动端。
- 生产级 auth / JWT。
- Phase 08 所有原计划工具的完整缺口收口。

## 下一阶段建议

下一阶段建议正式进入 Phase 08：Agent Tools 补齐与收口。

Phase 08 不应重复实现已存在的 Tool Registry、Tool Executor、已完成只读 tools 或已完成 draft write tools。建议先执行 Agent Tools gap review，再按缺口补齐必要 tools，整理权限声明、schema 风险与 Agent API 前置契约。

## Source of Truth

- `README.md`：项目概览、当前阶段、已完成与未完成能力。
- `CODEX_IMPLEMENTATION_PLAN.md`：原始阶段计划与工程执行边界。
- `docs/architecture/PHASE_PROGRESS.md`：实际进度映射与阶段重叠说明。
- `docs/architecture/KNOWN_RISKS.md`：当前已知风险与暂不修改项。

## Phase 08 Closeout 更新

Phase 08 Final Review 已通过，当前 Phase 08 状态更新为：已完成。

Phase 08 实际完成内容：

- Phase 08.A：`alerts:create` 从 Phase 07 临时桥接收口为独立 `can_create_alerts` 权限。
- Phase 08.B：新增 Agent API 最小入口，支持 `daily_health_brief` 与 trace/tool_calls/safety_checks 查询。
- Phase 08.C：新增受控草稿入口 `symptom_draft_create` 与 `medical_event_draft_create`。
- Phase 08.D：新增受控提醒入口 `alert_create`。
- POST `/api/v1/agent/runs` 当前只允许 4 个受控 workflow：`daily_health_brief`、`symptom_draft_create`、`medical_event_draft_create`、`alert_create`。
- 仍未开放通用 tool execution。
- 仍未调用 LLM。
- 仍未实现 LangGraph/OCR/upload/RAG。
- 仍未实现前端。

下一阶段建议调整为：

- Phase 09：可用前端 / 调试页面。
- Phase 10：LLM Client 最小封装。
- Phase 11：LLM 安全增强 Agent 输出。
- Phase 12：LangGraph Workflows。
- Phase 13：文件上传 / OCR / 文档处理增强。
- Phase 14：RAG / 健康知识库。
- Phase 15：真实 Auth / 部署 / 产品化收口。

## 当前 Source of Truth 补充

- `README.md`：项目概览、当前阶段、已完成/未完成能力。
- `CODEX_IMPLEMENTATION_PLAN.md`：原始阶段计划与 Phase 08 后执行顺序调整说明。
- `docs/architecture/PHASE_PROGRESS.md`：实际 Phase 进度映射。
- `docs/architecture/PHASE_08_SCOPE_RECONCILIATION.md`：Phase 08 最终范围与边界。
- `docs/architecture/FEATURE_COVERAGE_MATRIX.md`：产品功能、普通 API、Agent Tool、Agent Workflow、前端页面和后续 Phase 的覆盖矩阵。
- `docs/frontend/FRONTEND_MVP_SCOPE.md`：Phase 09 前端 MVP / 调试页面范围。
- `docs/architecture/KNOWN_RISKS.md`：当前风险与后续 schema/product review 事项。

## Phase 09 更新

Phase 09 已开始执行可用前端 / 调试页面方向。

当前已完成：

- Phase 09.1：`apps/mobile` Expo + React Native + TypeScript 静态 UI 原型。
- Phase 09.1 Lightweight Review：修复 Expo Router typed routes 类型问题并通过前端验证。

当前执行：

- Phase 09.2：移动端静态交互与 API 契约准备。

Phase 09.2 仍不接真实后端 API，不实现 Auth/JWT，不调用 LLM，不实现 LangGraph/OCR/upload/RAG。正式 FastAPI 接入预计放在 Phase 09.3。

## Phase 09.3.A 更新

Phase 09.3.A：前端 API Client 基础与只读 Demo 数据接入已开始。

当前完成范围：

- `apps/mobile` 新增 `apiConfig`、`apiClient`、`backendApi`、`dataProvider`。
- 支持 `EXPO_PUBLIC_DATA_MODE=mock/api`，默认 mock。
- API mode 需要显式配置 `EXPO_PUBLIC_API_BASE_URL`。
- 使用 `X-Current-User-Id` demo header，不实现 Auth/JWT。
- 首页、家庭、成员详情、设置开发者区、AI 管家、今日简报、Agent Run 详情开始接入只读 demo 数据或 Agent 安全摘要。
- `daily_health_brief` 可通过移动端 provider 调用 `POST /api/v1/agent/runs`。

仍未完成：

- 写入类 workflow 真实接入。
- 真实 Auth/JWT。
- LLM、LangGraph、OCR/upload/RAG。
- 后端新功能或模型变更。

下一步建议：Phase 09.3.A Lightweight Review。

## Phase 09.3.B 更新

Phase 09.3.B：前后端联调环境与 Smoke Runbook 收口已执行。

新增：

- `docs/frontend/MOBILE_BACKEND_SMOKE_RUNBOOK.md`
- `scripts/smoke/mobile_backend_smoke.ps1`

验证结果：

- 系统 Python 3.11 的 `pip` 损坏，无法直接作为后端依赖安装入口。
- Docker Desktop engine 未运行，PostgreSQL compose smoke 未完成。
- 使用 Codex bundled Python + 临时 `.venv-smoke` + SQLite smoke DB 绕开本机环境问题。
- Alembic migration、demo seed、demo verify、`GET /health`、`daily_health_brief`、run/tool_calls/safety_checks 查询均已通过 smoke。
- 移动端 `api` mode Web dev server 可启动并返回 HTTP 200。

边界保持：

- 写入类 workflow 仍未接入移动端真实后端。
- 未实现 Auth/JWT。
- 未实现 LLM、LangGraph、OCR/upload/RAG。
- 未修改后端业务代码、API 路由、模型或 migration。

下一步建议：Phase 09.3.C，围绕移动端只读 API 体验打磨与真机联调确认，不进入写入 workflow。

## Phase 09.3.C 更新

Phase 09.3.C：移动端只读 API 体验打磨与真机联调确认已执行。

完成范围：

- 补充 API / mock / 待接入状态标识。
- 补充 API loading / error / empty 展示。
- 首页、家庭页、成员详情页、AI 管家页、Agent Run 详情页、设置页完成只读 API 体验打磨。
- 新增 Expo Go 真机手动 QA 清单：`docs/frontend/MOBILE_DEVICE_QA_CHECKLIST.md`。

边界保持：

- 写入类 workflow 仍为 mock。
- 未接入 `symptom_draft_create`、`medical_event_draft_create`、`alert_create` 的真实调用。
- 未实现 Auth/JWT。
- 未实现 LLM、LangGraph、OCR/upload/RAG。
- 未修改后端业务代码、后端 API、模型或 migration。

剩余事项：

- 真机 Expo Go 需要用户按 QA checklist 手动视觉走查。
- PostgreSQL/Docker 路径仍待 Docker Desktop engine 可用后复验。

下一步建议：Phase 09.3.C Lightweight Review。

## Phase 09.3.D 更新

Phase 09.3.D：移动端写入类 Agent workflow 受控接入已执行。

完成范围：

- `apps/mobile` 在 `api` mode 下接入 `symptom_draft_create`。
- `apps/mobile` 在 `api` mode 下接入 `medical_event_draft_create`。
- `apps/mobile` 在 `api` mode 下接入 `alert_create`。
- 3 个写入类 workflow 均只通过 `POST /api/v1/agent/runs` 固定 workflow 调用。
- preview 使用 `confirmation=false`，页面明确不会写入。
- confirm 使用 `confirmation=true`，只创建待确认草稿或普通健康提醒。
- Agent Run 详情可查看写入 workflow 的 trace、tool_calls、safety_checks 安全摘要。
- 新增写入 workflow smoke 脚本：`scripts/smoke/mobile_write_workflows_smoke.ps1`。

边界保持：

- 未开放通用 tool execution。
- 未允许页面传 `tool_name` 或 `input_data`。
- 草稿列表和正式确认入库仍未真实接入。
- 未实现真实 Auth/JWT。
- 未调用 LLM。
- 未实现 LangGraph/OCR/upload/RAG。
- 未修改后端业务代码、后端 API、模型或 migration。

剩余事项：

- 真机 Expo Go 需要用户按 QA checklist 手动视觉走查。
- PostgreSQL/Docker 路径仍待 Docker Desktop engine 可用后复验。

下一步建议：Phase 09.3.D Lightweight Review。

## Phase 09.3.E 更新

Phase 09.3.E：写入流程 UI 打磨与真机 QA 修补已执行。

完成范围：

- 统一写入 workflow 页面 mock/api、preview/confirm、loading、success/error、安全阻断状态展示。
- `create-symptom-draft`、`create-health-event-draft`、`create-alert` 使用统一状态卡和安全结果摘要。
- Agent Run 详情强化 workflow、status、trace、tool_calls、safety_checks 的安全摘要展示。
- 设置页开发者调试区补充写入 workflow 接入状态和真机访问提示。
- 新增 `docs/frontend/WRITE_WORKFLOW_QA_CHECKLIST.md`。

边界保持：

- 未修改后端业务代码。
- 未新增后端 API、migration 或 model。
- 未开放通用 tool execution。
- 未允许页面传 `tool_name` 或 `input_data`。
- 草稿列表与正式确认入库仍未真实接入。
- 未实现 Auth/JWT。
- 未调用 LLM。
- 未实现 LangGraph/OCR/RAG。

下一步建议：Phase 09.3 Batch Review。

## Phase 09.3 Batch Review 更新

Phase 09.3 Batch Review 已完成基础验证。

验证范围：

- 移动端仍支持 mock/api mode。
- 只读 demo 数据、`daily_health_brief`、Agent run / tool_calls / safety_checks 查询可用。
- `symptom_draft_create`、`medical_event_draft_create`、`alert_create` 的 preview / confirm smoke 通过。
- 移动端不开放通用 tool execution。
- 移动端不允许页面传 `tool_name` 或 `input_data`。
- 草稿列表和正式确认入库仍未真实接入。

边界保持：

- 未修改后端业务代码。
- 未新增后端 API、migration 或 model。
- 未实现 Auth/JWT。
- 未调用 LLM。
- 未实现 LangGraph/OCR/upload/RAG。

## Phase 09.4 + Phase 09 Final Review 更新

Phase 09.4：移动端 MVP 闭环、真机问题修补与前端 MVP 最终验收已执行。

完成范围：

- 首页、家庭页、成员详情、AI 管家页、写入 workflow 页面、Agent Run 详情、草稿页、设置页完成 MVP 演示路径收口。
- 写入 workflow 页面继续明确 mock/api、preview/confirm、loading、success、error 与 safety blocked 状态。
- 设置页开发者调试区展示 data mode、API Base URL、`X-Current-User-Id`、`/health`、Agent workflow 接入状态和未完成功能。
- 新增 `docs/frontend/MOBILE_MVP_DEMO_SCRIPT.md`。
- 新增 `docs/frontend/MOBILE_MVP_ACCEPTANCE_CHECKLIST.md`。
- 新增 `docs/frontend/PHASE_09_FINAL_REVIEW.md`。
- 更新 README、移动端 README、前端 runbook、MVP scope、设备 QA、写入 workflow QA、Feature Coverage Matrix 与 Known Risks。

Phase 09 结论：

- Phase 09 可以视为移动端 MVP 已完成。
- 移动端 MVP 可演示，但不是生产发布包。
- 真机 Expo Go 视觉 QA 仍需要用户手动完成。
- 下一阶段建议进入 Phase 10：LLM Client 最小封装。

## Phase 10.A 更新

Phase 10.A：LLM Client 最小封装已执行。

完成范围：

- 新增 `backend/app/llm` 模块。
- 新增 `mock` provider，默认不请求外部网络。
- 新增 `openai_compatible` provider，预留 OpenAI-compatible chat completions 接入。
- 新增统一入口 `get_llm_client(settings)`、`LLMClient.generate_text(...)`、`LLMClient.chat(...)`。
- 新增 LLM request/response schema 与错误类型。
- 新增 `docs/architecture/LLM_CLIENT_DESIGN.md`。

边界保持：

- 默认 `LLM_ENABLED=false`。
- 默认 `LLM_PROVIDER=mock`。
- 未接入 `daily_health_brief`。
- 未修改 Agent workflow、Tool Executor 或 Agent API。
- 未修改前端。
- 未新增数据库 migration 或 model。
- 未实现 LangGraph/OCR/RAG。
- 未实现 Auth/JWT。

下一步建议：Phase 10.B，围绕 LLM Client 轻量验收或受控 workflow 接入前的 safety 契约审查。
