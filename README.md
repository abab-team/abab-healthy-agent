# Family Health Agent

## Current Status Summary (after Phase 24)

The project has completed **Phase 24: Free Text Record and Doctor Visit Summary Workflows**.

- Added `free_text_record_workflow` as a controlled Agent workflow for one-sentence health notes.
- Preview mode does not write business data; confirm mode creates only a pending health-record draft through the existing ToolExecutor path.
- Added `doctor_visit_summary_workflow` as a read-only doctor-visit preparation package based on system records.
- The doctor summary uses read-only tools for blood pressure, symptoms, medical events, documents, and alerts, and does not write reports, drafts, or formal health facts.
- Existing public workflow aliases remain unchanged: `symptom_draft_create`, `medical_event_draft_create`, and `alert_create` still map to their controlled Phase 08 workflows.
- No generic tool execution was opened, and frontend callers still must not pass `tool_name` or `input_data`.
- No new migration/model was added; no LLM, LangGraph, or Memory path directly queries DB, calls tools, or writes data.
- All Agent-facing health text remains based on system records and must not replace doctor judgment.
- Next phase: Phase 25, archive trends and data import foundation.

## Current Status Summary (after Phase 21)

The project has completed **Phase 21: Reflection / Critic**.

- Phase 20 added Prompt Registry, controlled LLM Planner, plan validation, and optional answer composition.
- Phase 21 adds a rule-first answer critic layer for `chat_workflow`.
- The critic checks medical safety boundaries, system-record coverage, permission-block wording, debug leakage, and simple count grounding.
- Unsafe or insufficiently grounded answers are rewritten with a safe system-record-only response before final output safety.
- `RULE_CRITIC_ENABLED=true` by default; `LLM_CRITIC_ENABLED=false` by default.
- The critic does not query DB, call tools, write business data, choose users, or bypass ToolExecutor / Permission / SafetyPolicy.
- General tool execution remains closed. Frontend must not pass `tool_name` / `input_data`.

## Current Status Summary (after Phase 22)

The project has completed **Phase 22: Stateful LangGraph Orchestration**.

- LangGraph remains optional and disabled by default.
- `chat_workflow` can now run through a safe graph state pipeline with nodes for memory loading, input safety, rule parse, plan validation, permission gate delegation, tool execution delegation, answer composition, critic review, output safety, memory update, and trace recording.
- Tool execution still happens only through the existing workflow and ToolExecutor.
- LangGraph does not directly query DB, call tools, write health data, choose users, or bypass permission and safety checks.
- Graph summaries are safe display summaries only and must not contain raw prompt, raw response, token/key/password, file path, OCR full text, SQL, traceback, `tool_name`, or `input_data`.

## Current Status Summary (after Phase 23)

The project has completed **Phase 23: Agent Evaluation Harness**.

- Added a deterministic synthetic evaluation set with 220 cases covering golden health queries, multi-turn memory follow-ups, permission boundaries, and medical-safety red-team prompts.
- Added a local eval runner and Markdown report.
- The harness reports intent accuracy, tool accuracy, safety pass rate, permission pass rate, and answer grounding rate.
- Evaluation does not use real user data, external LLM calls, generic tool execution, or business-data writes.

## 当前状态摘要（Phase 20 后）

当前已完成到 **Phase 20：Prompt Registry + LLM-assisted Planner**。

- Phase 18 已完成移动端信息架构重排。
- Phase 19 已完成 Agent session / messages / memory foundation，支持连续追问与安全偏好记忆。
- Phase 20 已新增版本化 Prompt Registry、受控 LLM Planner、Plan Validator 与可选 Answer Composer。
- `chat` workflow 仍保持规则优先；只有规则解析 unknown 且 `LLM_PLANNER_ENABLED=true` 时，才会尝试 LLM 生成受控 JSON plan。
- LLM 不直接选择 `tool_name` / `input_data`，不决定 `current_user_id` / `family_id` / `target_user_id`，不查数据库、不调工具、不写业务数据。
- 系统校验 plan 后才映射白名单工具并通过 ToolExecutor 执行。
- `LLM_PLANNER_ENABLED=false`、`LLM_ANSWER_COMPOSER_ENABLED=false` 为默认值。
- 当前仍不开放通用 tool execution，不允许前端传 `tool_name` / `input_data`。
- 所有健康回答仍必须基于系统内记录，不替代医生判断。

Family Health Agent 是一个面向家庭日常健康资料管理的移动端 Agent MVP。它支持家庭成员健康资料整理、家庭共享权限、文档上传与 mock OCR 预览、受控 Agent workflow、内部 RAG 检索增强、可选 LLM 健康简报，以及可追踪的 trace / tool calls / safety checks。

本项目不是医疗诊断系统，不提供处方、剂量、停药或自动急救建议。所有健康输出都应理解为“根据系统内记录进行整理”，不能替代医生判断或治疗建议。

## 当前阶段

当前已完成到 **Phase 19：Agent Memory 能力增强**。

Phase 18 完成了移动端信息架构重排；Phase 19 在 Phase 16/17 的自然语言健康查询基础上，新增了安全的 Agent session 与 memory 能力：

- `chat` workflow 支持 `session_id`，可连续追问系统内健康记录。
- 支持“那上个月呢 / 我妈呢 / 和刚才一样”等短期上下文继承。
- 新增可查看、可删除的安全长期偏好记忆。
- Memory 不保存未经确认的医疗事实，不作为正式健康事实来源。
- 仍不开放通用 tool execution，不允许用户传 `tool_name` / `input_data`。
- LangGraph 仍为可选编排增强，默认关闭；Phase 20 尚未开始。

## 当前能力

后端：

- FastAPI + SQLAlchemy + Alembic。
- Auth/JWT 最小闭环：register / login / refresh / logout / me。
- 家庭、成员、共享权限、健康档案、健康数据、症状、医疗事件、文档、报告、提醒等模块。
- 统一错误响应、输入清洗、权限守卫、data access logs。
- Agent Runtime / Tool Registry / Tool Executor / Safety Policy。
- Agent trace / safety checks / tool calls 查询。
- 受控 Agent workflows：
  - `chat`
  - `daily_health_brief`
  - `symptom_draft_create`
  - `medical_event_draft_create`
  - `alert_create`
- 自然语言健康查询工具：
  - 指标 / 血压 / 症状 / 健康事件 / 文档 / 提醒的系统内安全摘要查询。
- LangGraph 可选编排：
  - 默认关闭，仅 `chat` workflow 可选记录安全节点摘要。
- LLM Client：默认关闭，`daily_health_brief` 可选接入并带 fallback。
- 文档上传、document processing job、mock OCR preview。
- 内部 RAG simple retrieval：默认关闭，只返回系统内安全摘要和 citations。

移动端：

- Expo + React Native + TypeScript。
- mock / api / api-auth mode。
- 首页、家庭、成员详情、AI 管家、设置、Agent Run 详情。
- AI 管家自然语言查询系统内健康记录。
- 写入类 workflow 的 preview / confirm 体验。
- 文档处理与 OCR preview 的 MVP 展示入口。

工程：

- demo seed / verify。
- 后端 API tests。
- 前端 typecheck / lint / web export。
- smoke scripts。
- deployment / QA / portfolio 文档。

## 尚未完成

- 正式生产部署。
- 真实 OCR provider。
- OCR worker 队列。
- RAG 持久化索引、真实 embedding provider、vector DB。
- 外部医学知识库。
- 生产级 LangGraph workflow 与复杂多节点状态机。
- 真实推送通知。
- 移动端生产发布包。
- 完整真机视觉 QA。
- 草稿正式确认入库的移动端闭环。

## 快速启动后端

```powershell
$env:PYTHONPATH="backend"
$env:DATABASE_URL="sqlite:///backend/storage/local/demo.sqlite3"
python -m alembic -c backend/alembic.ini upgrade head
python backend/scripts/seed_demo_data.py
python backend/scripts/verify_demo_data.py
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

验证：

```powershell
curl http://127.0.0.1:8000/health
```

## 快速启动移动端

```powershell
cd apps/mobile
npm install
npm run web
```

Expo Go 真机访问电脑后端时，不能使用 `localhost`。请在 `apps/mobile/.env` 中配置电脑局域网 IP：

```text
EXPO_PUBLIC_DATA_MODE=api-auth
EXPO_PUBLIC_API_BASE_URL=http://<电脑局域网IP>:8000
```

## 关键文档

部署与配置：

- `docs/deployment/MVP_DEPLOYMENT_RUNBOOK.md`
- `docs/deployment/ENVIRONMENT_VARIABLES.md`
- `docs/deployment/PRODUCTION_SAFETY_CHECKLIST.md`
- `docs/deployment/DOCKER_RUNBOOK.md`

移动端与 QA：

- `docs/frontend/MOBILE_REAL_DEVICE_QA.md`
- `docs/frontend/MOBILE_DEVICE_QA_CHECKLIST.md`
- `docs/frontend/MOBILE_UX_FIX_LOG.md`
- `docs/frontend/WRITE_WORKFLOW_QA_CHECKLIST.md`

Demo 与作品集：

- `docs/demo/MVP_DEMO_SCRIPT.md`
- `docs/demo/DEMO_DATA_GUIDE.md`
- `docs/demo/SCREENSHOT_CHECKLIST.md`
- `docs/demo/FEATURE_WALKTHROUGH.md`
- `docs/portfolio/PROJECT_OVERVIEW.md`
- `docs/portfolio/TECHNICAL_HIGHLIGHTS.md`
- `docs/portfolio/ARCHITECTURE_SUMMARY.md`
- `docs/portfolio/INTERVIEW_TALK_TRACK.md`

架构与风险：

- `docs/architecture/PHASE_PROGRESS.md`
- `docs/architecture/KNOWN_RISKS.md`
- `docs/architecture/RAG_DESIGN.md`
- `docs/architecture/CHAT_WORKFLOW_DESIGN.md`
- `docs/architecture/HEALTH_QUERY_TOOLS.md`
- `docs/architecture/LANGGRAPH_DESIGN.md`
- `docs/architecture/LLM_CLIENT_DESIGN.md`
- `docs/architecture/AUTH_JWT_DESIGN.md`

## Smoke 验证

推荐顺序：

```powershell
python -m compileall backend/app backend/tests
python -m unittest discover backend/tests/api -v
scripts/smoke/mobile_backend_smoke.ps1
scripts/smoke/auth_smoke.ps1
scripts/smoke/document_upload_smoke.ps1
scripts/smoke/document_processing_smoke.ps1
scripts/smoke/ocr_document_smoke.ps1
scripts/smoke/rag_retrieval_smoke.ps1
scripts/smoke/rag_agent_smoke.ps1
scripts/smoke/chat_health_query_smoke.ps1
scripts/smoke/langgraph_health_query_smoke.ps1
```

验证后不要提交 smoke DB、storage 文件、`__pycache__`、`.env`、API key 或用户附件。

## 安全边界

- LLM 不决定 `current_user_id`、`family_id`、`target_user_id`。
- Agent 不直接访问数据库。
- Tool 不直接访问数据库，只能调用 service。
- 家人数据访问必须经过 family permission。
- 写入类 workflow 必须 preview / confirm。
- OCR/RAG/LLM 不直接写正式健康事实。
- 系统不输出医学诊断、处方、剂量、停药建议。
- 普通提醒不是急救服务。

## Phase 15 后建议

先完成：

1. 用户本人真机完整体验。
2. 录屏或截图。
3. 作品集页面整理。
4. 面试讲解练习。

后续功能型阶段建议：

- Phase 16.A：真实 OCR Provider 受控接入。
- Phase 16.B：RAG 持久化索引与权限同步。
- Phase 16.C：PostgreSQL / 云部署。
- Phase 16.D：LangGraph Workflow 重构。
