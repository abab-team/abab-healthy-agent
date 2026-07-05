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
