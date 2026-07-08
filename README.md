# Family Health Agent

Family Health Agent 是一个面向家庭日常健康资料管理的移动端 Agent MVP。它支持家庭成员健康资料整理、家庭共享权限、文档上传与 mock OCR 预览、受控 Agent workflow、内部 RAG 检索增强、可选 LLM 健康简报，以及可追踪的 trace / tool calls / safety checks。

本项目不是医疗诊断系统，不提供处方、剂量、停药或自动急救建议。所有健康输出都应理解为“根据系统内记录进行整理”，不能替代医生判断或治疗建议。

## 当前阶段

当前已完成到 **Phase 15：部署 / 真机 QA / 作品集展示收口**。

Phase 15 的目标不是继续新增大功能，而是让项目达到：

- 后端可按 runbook 启动。
- demo 数据可复现。
- 移动端可连接真实 API。
- 核心 smoke 可通过。
- 真机 QA 路径清楚。
- 作品集和 demo 讲解材料完整。

## 当前能力

后端：

- FastAPI + SQLAlchemy + Alembic。
- Auth/JWT 最小闭环：register / login / refresh / logout / me。
- 家庭、成员、共享权限、健康档案、健康数据、症状、医疗事件、文档、报告、提醒等模块。
- 统一错误响应、输入清洗、权限守卫、data access logs。
- Agent Runtime / Tool Registry / Tool Executor / Safety Policy。
- Agent trace / safety checks / tool calls 查询。
- 受控 Agent workflows：
  - `daily_health_brief`
  - `symptom_draft_create`
  - `medical_event_draft_create`
  - `alert_create`
- LLM Client：默认关闭，`daily_health_brief` 可选接入并带 fallback。
- 文档上传、document processing job、mock OCR preview。
- 内部 RAG simple retrieval：默认关闭，只返回系统内安全摘要和 citations。

移动端：

- Expo + React Native + TypeScript。
- mock / api / api-auth mode。
- 首页、家庭、成员详情、AI 管家、设置、Agent Run 详情。
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
- LangGraph workflow。
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
