# Phase Progress

## Current Status Summary (after Phase 25)

Current source of truth: the project has completed **Phase 25: Archive Trends and Data Import Foundation**.

- Phase 25 turns the archive area into a long-term health-record entry point.
- Backend health-data service now provides safe trend summaries for metrics and blood pressure based on existing system records.
- Backend API now supports self archive trend retrieval plus import preview / confirm for CSV/Excel-style rows.
- Import preview writes no formal health data; confirm writes only rows that pass validation through existing service methods.
- Mobile archive page now displays trend cards, a health timeline, document/draft entries, and an import preview/confirm panel.
- The implementation does not add HealthKit / Health Connect, real device sync, diagnosis, prescription, dosage, stop-medication guidance, migration/model, or generic tool execution.
- Next phase: Phase 26, production deployment and security readiness.

## Current Status Summary (after Phase 24)

Current source of truth: the project has completed **Phase 24: Free Text Record and Doctor Visit Summary Workflows**.

- Phase 24 adds `free_text_record_workflow` for controlled one-sentence health note drafting.
- Preview mode records no formal business data; confirm mode creates only a pending health-record draft through the existing ToolExecutor and service boundary.
- Phase 24 adds `doctor_visit_summary_workflow` as a read-only preparation package based on system records.
- Doctor summary generation uses read-only tools for blood pressure, symptoms, medical events, documents, and alerts.
- The workflow output is only a system-record summary for communication preparation and does not provide medical judgment or treatment instructions.
- Existing controlled workflow aliases remain stable: `symptom_draft_create`, `medical_event_draft_create`, and `alert_create`.
- No generic tool execution, `tool_name`, or `input_data` entry point was opened.
- No LLM, LangGraph, or Memory path directly queries DB, directly calls tools, or writes business data.
- No migration/model was added in this phase.
- Next phase: Phase 25, archive trends and data import foundation.

## Current Status Summary (after Phase 21)

Current source of truth: the project has completed **Phase 21: Reflection / Critic**.

- Phase 18: mobile information architecture alignment completed.
- Phase 19: Agent memory foundation completed.
- Phase 20: Prompt Registry and controlled LLM Planner completed.
- Phase 21: rule-first answer critic, optional LLM critic switch, safe rewrite, and critic safety-check trace summary completed.
- Defaults remain conservative: `RULE_CRITIC_ENABLED=true`, `LLM_CRITIC_ENABLED=false`, `LLM_PLANNER_ENABLED=false`, `LLM_ANSWER_COMPOSER_ENABLED=false`.
- The critic does not query DB, call tools, write data, choose `current_user_id` / `family_id` / `target_user_id`, or bypass ToolExecutor / Permission / SafetyPolicy.
- Next phase: Phase 22, stateful LangGraph orchestration, only if it preserves existing safety and permission boundaries.

## Current Status Summary (after Phase 22)

Current source of truth: the project has completed **Phase 22: Stateful LangGraph Orchestration**.

- Phase 22 upgrades the optional LangGraph adapter from a thin summary wrapper to a safe state-node pipeline for `chat_workflow`.
- Implemented nodes include memory loading, input safety, rule parse, confidence routing, LLM-plan delegation marker, plan validation, clarification route, permission gate delegation, ToolExecutor-backed execution, answer composition, critic review, output safety, memory update, trace recording, and fallback.
- Defaults remain conservative: `LANGGRAPH_ENABLED=false`, `LANGGRAPH_CHAT_QUERY_ENABLED=false`, `LANGGRAPH_STRICT_MODE=false`.
- LangGraph does not directly query DB, call tools, write business data, choose user/family/target IDs, or bypass ToolExecutor / Permission / SafetyPolicy.
- Next phase: Phase 23, Agent Evaluation harness.

## Current Status Summary (after Phase 23)

Current source of truth: the project has completed **Phase 23: Agent Evaluation Harness**.

- Added `backend/tests/evaluation/agent_eval_cases/*.jsonl` with 220 synthetic cases.
- Added a deterministic eval runner and local test coverage.
- Evaluation dimensions include intent, member/time/tool selection, multi-turn memory follow-up metadata, permission boundary cases, safety red-team prompts, and answer grounding.
- Latest local result: 220 passed / 0 failed.
- No real user data, external LLM call, generic tool execution, migration/model, or business-data write was added.
- Next phase: Phase 24, free text record and doctor summary workflows.

## 当前状态摘要（Phase 20 后）

当前项目已完成到 **Phase 20：Prompt Registry + LLM-assisted Planner**。

- Phase 18：移动端信息架构与页面重排已完成。
- Phase 19：Agent Memory foundation 已完成，包含 `agent_sessions`、`agent_messages`、`agent_memory_items`、短期上下文继承、长期安全偏好记忆、memory list/delete API 与移动端连续对话入口。
- Phase 20：新增版本化 Prompt Registry、planner / answer composer / memory extractor / critic prompt 模板、LLM Planner Service、Plan Validator 与可选 Answer Composer。
- `chat` workflow 保持 rule-first；规则命中时不调用 LLM；规则 unknown 且 `LLM_PLANNER_ENABLED=true` 时才尝试 LLM planner。
- LLM planner 只能输出受控 JSON plan，不允许输出 `tool_name` / `input_data` / user id / family id / SQL / file path。
- 系统校验 plan 后才映射白名单工具，并继续通过 ToolExecutor / Permission / Safety / Trace 边界执行。
- 默认配置仍为 `LLM_PLANNER_ENABLED=false`、`LLM_ANSWER_COMPOSER_ENABLED=false`、`PROMPT_REGISTRY_ENABLED=true`。
- 未开放通用 tool execution，未允许前端传 `tool_name` / `input_data`，未让 LLM / LangGraph / Memory 直接查 DB、调 tool 或写业务数据。
- 下一阶段建议进入 Phase 21：Reflection / Critic。

## 当前状态摘要（Phase 19 后）

当前项目已完成到 **Phase 19：Agent Memory 能力增强**。

- Phase 18 已完成：移动端信息架构重排，底部导航调整为：首页 / 档案 / 家庭 / AI 管家 / 我的；新增档案页；AI 管家页回到对话与常用能力；家庭页权限卡片补齐；开发者调试弱化到“我的”页折叠区。
- Phase 19 已完成：新增 `agent_sessions`、`agent_messages`、`agent_memory_items`；`chat` workflow 支持 session 上下文；支持“那上个月呢 / 我妈呢 / 和刚才一样 / 换成最近 30 天”等短期指代；新增 Memory list/delete API；移动端支持连续对话和 AI 记忆管理入口。
- 当前仍未进入 Phase 20；尚未实现 Prompt Registry 或 LLM-assisted Planner。
- Memory 只保存安全摘要和偏好，不保存未经确认的医疗事实，不作为正式健康事实来源。
- 所有健康回答仍需表达为“基于系统内记录，不替代医生判断”。

## 当前状态摘要（Phase 17 后）

本文档顶部为当前 source of truth；下方早期条目保留为历史阶段记录，不代表最新项目状态。

当前项目已完成到 **Phase 17：LangGraph 可选编排增强**。

### Phase 09-15 完成摘要

| Phase | 当前状态 | 摘要 |
| --- | --- | --- |
| Phase 09 | 已完成 | Expo 移动端 MVP、mock/api/api-auth mode、只读 API、受控写入 workflow、Agent Run 调试摘要、移动端演示路径。 |
| Phase 10 | 已完成 | LLM Client 最小封装，`daily_health_brief` 可选 LLM；默认关闭，失败回退规则简报。 |
| Phase 11 | 已完成 | 真实 provider 验证 runbook、LLM 输出质量评估与文档收口。 |
| Phase 12 | 已完成 | Auth/JWT、Bearer token、refresh/logout、移动端登录态接入。 |
| Phase 13 | 已完成 | 文档上传、document processing job、mock OCR preview、OCR 到健康事件草稿的受控链路。 |
| Phase 14 | 已完成 | 内部 RAG simple retrieval、citations、RAG API、Agent 内部上下文增强；默认关闭，未接外部医学知识库。 |
| Phase 15 | 已完成 | 部署 runbook、环境变量说明、生产安全清单、Docker 说明、真机 QA 文档、demo/截图/作品集材料与最终验收文档。 |
| Phase 16 | 已完成 | 新增 `chat` workflow、deterministic intent/time/member parser、系统内只读健康查询 tools、移动端 AI 管家自然语言入口与 smoke。 |
| Phase 17 | 已完成 | 新增默认关闭的 LangGraph adapter、graph state 安全校验、chat graph node summary、Agent Run 图编排摘要与 smoke。 |

### 当前已具备能力

- 后端业务模块、API、权限闭环、data access logs、统一错误响应、输入清洗。
- Auth/JWT 与移动端 `api-auth` 登录态。
- 移动端 MVP：家庭、成员、AI 管家、设置、写入 workflow、Agent Run 详情。
- Agent Runtime、Tool Registry、Tool Executor、Safety Policy、trace/tool_calls/safety_checks。
- 受控 Agent workflow：`chat`、`daily_health_brief`、`symptom_draft_create`、`medical_event_draft_create`、`alert_create`。
- 自然语言健康查询：只查询系统内记录，固定映射到只读工具，不开放 `tool_name` / `input_data`。
- LangGraph 可选编排增强：默认关闭；当前只为 `chat` workflow 记录安全 graph node summary。
- 文档上传、document processing job、mock OCR preview。
- 内部 RAG simple retrieval 与 Agent 上下文增强。
- 部署、QA、demo、作品集文档。

### 当前仍未完成

- 生产级 LangGraph workflow 与复杂多节点状态机。
- 真实 OCR provider。
- RAG 持久化索引、真实 embedding provider、vector DB。
- 移动端生产发布包。
- 完整真机视觉 QA。
- 草稿正式确认入库的移动端完整闭环。
- 生产级密钥管理、HTTPS、正式隐私策略和云部署。

### 下一步建议

下一步不建议继续加新功能。建议先完成：

1. 用户本人真机 QA。
2. 录屏 / 截图。
3. 作品集页面整理。
4. 演示讲解稿和面试讲解练习。

如后续继续开发，建议进入 Phase 18：生产化部署与真实设备 QA 收口，或按专项 review 推进真实 OCR provider / RAG 持久化索引。

## 历史阶段记录

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

## Phase 10.B 更新

Phase 10.B：`daily_health_brief` 可选接入 LLM 已执行。

完成范围：

- 新增 `DAILY_BRIEF_USE_LLM=false` 配置项。
- `daily_health_brief` 仅在 `LLM_ENABLED=true` 且 `DAILY_BRIEF_USE_LLM=true` 时尝试调用 LLM。
- LLM 输入只使用只读 tools 已整理后的结构化摘要。
- LLM 输出先经过 output safety 检查；不安全、空输出、配置错误或 provider 失败时回退规则简报。
- Agent run message 中记录安全调试摘要：`llm_used`、`llm_provider`、`llm_model`、`fallback_used`、`fallback_reason`。

边界保持：

- 默认行为不变，默认仍走规则简报。
- 未接入其他 workflow。
- 未修改前端。
- 未实现 LangGraph/OCR/RAG。
- 未实现 Auth/JWT。
- 未新增数据库 migration 或 model。
- 未新增业务 API。

下一步建议：Phase 10.C，围绕 LLM 接入 lightweight review 或 prompt/safety 契约验收。

## Phase 10.C 更新

Phase 10.C：LLM 输出安全、fallback 与文档收口已执行。

完成范围：

- 收紧 `daily_health_brief` 的 LLM system prompt，明确不替代医生、不诊断、不处方、不给剂量、不建议停药、不判断正常/异常/高风险/低风险、不承诺急救或自动联系医院/家人。
- 确认 LLM user prompt 只使用只读 tools 汇总后的结构化摘要，不传 `raw_text`、`symptom_text`、`raw_extracted_text`、`file_path`、API key、traceback 或 SQL。
- 对 provider error、timeout、空输出、response schema 不完整、unsafe 输出等场景统一 fallback 到规则简报。
- unsafe LLM 输出不会返回给用户，也不会写入 trace/debug。
- LLM 分支会在 `agent_safety_checks` 中记录安全摘要，例如 `llm_used`、`fallback_used`、`fallback_reason`、`safety_filtered`。
- 补充 daily health brief LLM safety/fallback 单元测试。

边界保持：

- 默认 `LLM_ENABLED=false` 且 `DAILY_BRIEF_USE_LLM=false`，默认 `daily_health_brief` 行为不变。
- 仍仅 `daily_health_brief` 可选使用 LLM。
- 未接入 `symptom_draft_create`、`medical_event_draft_create`、`alert_create` 或其他 workflow。
- 未修改前端。
- 未实现 Auth/JWT。
- 未实现 LangGraph/OCR/RAG。
- 未新增数据库 migration 或 model。
- 未新增业务 API。

下一步建议：Phase 10 Batch Review，对 Phase 10.A/10.B/10.C 的 LLM client、可选接入、安全收口和默认 smoke 做总体验收。
## Phase 11 更新

Phase 11：真实 LLM Provider 受控验证与 Agent 输出质量评估已执行。

完成范围：
- Phase 11.A：新增真实 provider smoke runbook 与 `scripts/smoke/llm_provider_smoke.*`，默认 mock，不联网，不需要真实 key。
- Phase 11.B：新增 `daily_health_brief` LLM 质量评估 harness，使用合成结构化摘要覆盖 normal、empty、multi-member、follow-up reminder、safety-sensitive 用例。
- Phase 11.C：新增 Phase 11 provider verification、real provider runbook、daily brief evaluation 文档，说明安全、fallback、trace/debug、成本、延迟、稳定性风险。

边界保持：
- 未修改前端。
- 未接入其他 workflow。
- 未实现 Auth/JWT。
- 未实现 LangGraph/OCR/RAG。
- 未新增数据库 migration/model。
- 未新增后端业务 API。
- 未开放通用 tool execution。
- 未提交 `.env`、API key、真实 provider 原始输出或用户附件。

下一阶段建议：Phase 12：Auth/JWT 与用户会话，先补齐真实身份边界，再扩大 LLM/LangGraph 能力。

## Phase 12.A 更新

Phase 12.A：Auth/JWT 与用户会话地基已执行。

完成范围：
- 新增 `backend/app/modules/auth` 模块，包含 auth API、schema、service、repository、password、token 与异常定义。
- 新增最小 Auth API：
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/refresh`
  - `POST /api/v1/auth/logout`
  - `GET /api/v1/auth/me`
- 复用现有 `users`、`login_sessions`、`refresh_tokens` 表，不新增 migration/model。
- 新增 PBKDF2-SHA256 密码哈希与 HMAC-SHA256 JWT access token。
- refresh token 原文不入库，只保存哈希；refresh 会轮换 token，logout 会撤销 refresh token。
- demo seed 用户写入开发用密码哈希，auth smoke 可验证 login/me/refresh/logout。
- 新增 `docs/architecture/AUTH_JWT_DESIGN.md` 与 `scripts/smoke/auth_smoke.ps1`。

边界保持：
- 默认 `AUTH_ENABLED=false`。
- 默认 `AUTH_DEMO_LOGIN_ENABLED=true`。
- 既有 `X-Current-User-Id` demo header 未移除，现有业务 API 尚未强制切换 JWT。
- 未修改前端。
- 未修改 Agent workflow、LLM、Tool Executor 或 LangGraph。
- 未新增 OAuth、短信验证码、邮箱验证、管理员 RBAC 或生产级账号策略。

## Phase 12.B 更新

Phase 12.B：替换 demo header 鉴权链路已执行。

完成范围：
- 统一 current user dependency 支持 `Authorization: Bearer <access_token>`。
- Bearer token 优先于 `X-Current-User-Id`。
- 无效 Bearer token 直接返回 401，不 fallback demo header。
- 新增 `AUTH_DEMO_HEADER_ENABLED` 配置，默认开发模式为 true。
- 当 `AUTH_DEMO_HEADER_ENABLED=false` 时，demo header 请求会被拒绝。
- Agent API 通过统一 current user dependency 使用 JWT 用户。
- family / permissions 权限检查仍独立生效。

边界保持：
- 未删除 demo header fallback。
- 未修改 Agent workflow、Tool Executor、LLM 或 LangGraph。
- 未修改数据库模型或 migration。

## Phase 12.C 更新

Phase 12.C：移动端登录态接入已执行。

完成范围：
- 新增 `/login` 登录页。
- 新增移动端 auth session store。
- `api-auth` mode 自动发送 `Authorization: Bearer`。
- access token 过期时尝试 refresh；refresh 失败后清理 session。
- 设置页显示 auth mode、当前用户摘要、token 短摘要和 logout。
- `mock` mode 与 `api-demo` mode 均保留。
- 新增 `scripts/smoke/mobile_auth_smoke.ps1`。

边界保持：
- 未实现 OAuth、短信验证码、邮箱验证、找回密码或复杂账号中心。
- 未开放通用 tool execution。
- 未修改后端业务模型或 migration。

## Phase 12.D 更新

Phase 12.D：Auth 安全、错误处理与文档收口已执行。

完成范围：
- 更新 `docs/architecture/AUTH_JWT_DESIGN.md`。
- 新增 `docs/architecture/AUTH_SECURITY_NOTES.md`。
- 新增 `docs/frontend/AUTH_MOBILE_RUNBOOK.md`。
- 新增 `docs/frontend/AUTH_QA_CHECKLIST.md`。
- 新增 `docs/architecture/PHASE_12_AUTH_FINAL_REVIEW.md`。
- 更新 README、移动端 README、Known Risks 与 smoke runbook。

Phase 12 结论：
- Phase 12 可以视为 Auth/JWT 与用户会话阶段完成。
- 生产前仍需关闭 demo header、设置强 JWT secret、补 Native SecureStore 和更完整账号安全策略。

下一阶段建议：Phase 13：文件上传 / OCR / 文档处理增强。
## Phase 13 更新

Phase 13：健康资料上传 / 文档处理 / mock OCR / 待确认健康事件草稿闭环已执行。

完成范围：
- 新增受控本地文档上传入口，支持 PDF/PNG/JPG/JPEG，拒绝未知 MIME、危险扩展名、超大文件与路径穿越文件名。
- 上传文件只保存内部 storage key，API response 不返回本机绝对路径或 `file_path`。
- 补齐 document processing job 查询接口，支持创建、查询、列表与安全失败原因。
- 新增 `backend/app/ocr` mock OCR 抽象，默认 `OCR_ENABLED=false`，显式开启后只生成安全预览与结构化 hints。
- mock OCR extraction result 默认不保存完整 `raw_extracted_text`。
- OCR result 可通过现有 `medical_event_draft_create` Agent workflow 生成 pending `medical_event_draft`。
- 未确认 preview 不写入草稿；确认后也只创建待确认草稿，不创建正式 `medical_event`。
- 新增 Phase 13 API 测试与 smoke 脚本。
- 移动端新增健康资料列表和文档处理详情的最小展示入口。

边界保持：
- 未实现真实 OCR provider。
- 未实现 OCR worker 队列。
- 未实现移动端原生文件选择器。
- 未生成诊断、处方、剂量建议或停药建议。
- 未将 OCR 结果直接写成正式健康事实。
- 未新增数据库 migration 或 model。
- 未开放通用 tool execution。

下一阶段建议：Phase 13 Batch Review，重点复核上传安全、OCR preview 安全、草稿边界、移动端文档处理展示与 smoke 链路。
## Phase 14 更新

Phase 14：内部 RAG 检索与 Agent 上下文增强已执行。

完成范围：

- 新增 `backend/app/rag/**`，包含 source policy、schemas、chunking、simple retrieval、动态内部索引和 Agent context helper。
- 新增 `POST /api/v1/rag/search`，只返回安全摘录、citation 和 source metadata，不生成医学回答。
- 新增 `RAG_ENABLED=false` 等配置项，默认关闭 RAG。
- `daily_health_brief` 在 RAG 开启时追加系统内 citation，失败时回退原规则简报。
- `medical_event_draft_create` 在 RAG 开启时追加安全 `structured_hints.rag_sources`，仍只创建待确认草稿。
- 新增 RAG 单测、API 测试、最小合成 evaluation 和 smoke 脚本。

边界保持：

- 未新增数据库 migration 或 model。
- 未接入真实 embedding provider。
- 未接入 vector DB。
- 未接入外部医学知识库。
- 未实现 RAG chatbot。
- 未修改移动端。
- 未开放通用 tool execution。
- 未允许 `tool_name` / `input_data`。
- 未让 RAG 写入正式健康事实。

下一阶段建议：Phase 15：RAG 检索质量、持久化索引与撤权同步策略 review。

## Phase 15 更新

Phase 15：部署 / 真机 QA / 作品集展示收口已执行。

完成范围：

- 新增 MVP 演示部署 runbook：`docs/deployment/MVP_DEPLOYMENT_RUNBOOK.md`。
- 新增环境变量说明：`docs/deployment/ENVIRONMENT_VARIABLES.md`。
- 新增生产安全清单：`docs/deployment/PRODUCTION_SAFETY_CHECKLIST.md`。
- 新增 Docker 开发演示说明：`docs/deployment/DOCKER_RUNBOOK.md`。
- 新增移动端真机 QA 文档与 UX 修补记录：`docs/frontend/MOBILE_REAL_DEVICE_QA.md`、`docs/frontend/MOBILE_UX_FIX_LOG.md`。
- 新增 demo 与作品集材料：`docs/demo/**`、`docs/portfolio/**`。
- README 已收口为当前可演示 MVP 入口，覆盖快速启动、能力边界、关键文档、smoke 和后续计划。
- 新增部署 smoke 辅助脚本：`scripts/smoke/deploy_mvp_smoke.ps1`、`scripts/smoke/mobile_lan_api_smoke.ps1`。

Phase 15 结论：

- 当前项目达到可演示 MVP 标准：本地/局域网运行路径清楚，移动端演示路径清楚，核心 smoke 可复现，作品集讲解材料完整。
- 当前仍不是正式生产上线版本。
- 真实手机扫码、触控体验、不同屏幕尺寸视觉 QA 仍需用户手动完成。
- 生产部署前仍需关闭 demo header、设置强密钥、配置 HTTPS/CORS/持久化 storage、完成隐私与安全 review。

下一步建议：

1. 用户本人执行 Expo Go 真机 QA。
2. 按 `docs/demo/SCREENSHOT_CHECKLIST.md` 完成截图/录屏。
3. 整理作品集页面。
4. 如继续功能开发，建议进入 Phase 16.A：真实 OCR Provider 受控接入。
