# Family Health Agent

Family Health Agent 是面向家庭长期使用的健康档案、家庭健康共享与受控 Agent 辅助系统。项目当前已完成到 **Phase 08 Final Review**：后端核心业务 API、权限闭环、API 安全、Agent Harness、Agent Tool Executor、第一批受控 Agent workflow 和 Agent API 最小入口已经可验证运行。

本项目不是医疗诊断系统。系统只做生活健康管理、资料整理、趋势提醒和就医沟通辅助，不输出医学诊断、处方建议、药物剂量建议、停药/换药建议，也不把“系统内无记录”表达成“现实没有问题”。

## 当前阶段

当前状态：

- Phase 00-08 已完成。
- Phase 08 已完成 Agent Tool 权限收口、Agent API 最小入口、受控草稿 workflow、受控提醒 workflow。
- Phase 09 已开始移动端可用前端方向；Phase 09.1 已完成 Expo 静态 UI 原型，Phase 09.2 正在推进静态交互与 API 契约准备。
- 当前不是完整产品，仍缺少正式前端、真实 Auth/JWT、LLM、LangGraph、OCR/upload/RAG 和生产部署收口。
- 下一阶段调整为 **Phase 09：可用前端 / 调试页面**，优先把已有后端 API 与 Agent API 变成可操作、可验收的产品闭环。

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

## 未完成能力

当前尚未完成：

- 正式 Web 前端。
- 移动端真实 API 联调与发布。
- 真实 Auth/JWT 登录体系。
- LLM Client。
- LangGraph workflow。
- OCR / upload / RAG。
- 生产部署、真实通知、真实设备接入。
- 通用 tool execution API。当前刻意不开放任意 `tool_name` / `input_data` 执行。

## 重要说明

当前不是“产品只有 4 个功能”。当前只是 **Agent API 对外开放了 4 个受控 workflow**。产品功能、普通 API、Agent Tool、Agent Workflow、前端页面是不同层级，后续会分别按功能覆盖矩阵推进。

功能覆盖与后续 Phase 映射请阅读：

- `docs/architecture/FEATURE_COVERAGE_MATRIX.md`
- `docs/frontend/FRONTEND_MVP_SCOPE.md`
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
