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
