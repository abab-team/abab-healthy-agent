# 技术亮点

## 1. 模块化单体后端

后端使用 FastAPI + SQLAlchemy + Alembic，按业务域拆分 `identity`、`family`、`permissions`、`health_profile`、`health_data`、`health_record`、`medical_timeline`、`document_center`、`document_processing`、`reports`、`alerts`、`audit` 等模块。

## 2. 家庭共享权限模型

家庭成员访问不是简单“登录即授权”。家人数据访问必须同时满足：

- 当前用户身份。
- `family_id`。
- 目标成员。
- 具体 permission type/action。

Agent 工具也使用同一权限入口。

## 3. Agent Runtime + Tool Executor

Agent 层不是直接调用数据库，而是通过：

- Runtime 创建 trace。
- Safety Policy 评估输入输出。
- Tool Registry 声明工具能力。
- Tool Executor 执行 confirmation、permission、tool_call 记录。
- Service 层执行业务逻辑。

## 4. preview / confirm 写入边界

写入类 workflow 不直接制造正式健康事实：

- `symptom_draft_create` 创建待确认症状草稿。
- `medical_event_draft_create` 创建待确认健康事件草稿。
- `alert_create` 创建普通健康提醒。

preview 不写入，confirm 也不自动确认正式健康事实。

## 5. LLM 可选接入与 fallback

LLM Client 支持 mock 和 OpenAI-compatible provider，但默认关闭。当前只有 `daily_health_brief` 可选使用 LLM，并且：

- 只接收结构化摘要。
- 输出经过 safety。
- 失败 fallback 到规则简报。
- trace/debug 不记录 raw prompt 或 raw response。

## 6. 文档处理与 mock OCR

Phase 13 提供安全上传、processing job、mock OCR preview 和 OCR 到 pending draft 的链路。API 不返回本机路径，OCR raw text 默认不存储。

## 7. 内部 RAG 检索

Phase 14 提供 simple/internal retrieval：

- 默认关闭。
- 只检索系统内安全摘要。
- 返回 safe excerpts 和 citations。
- 不接外部医学知识库。
- 不使用 vector DB。

## 8. 可验证工程闭环

项目包含：

- backend API tests。
- Agent/RAG/evaluation tests。
- smoke scripts。
- deployment runbook。
- mobile QA checklist。
- portfolio/demo materials。

