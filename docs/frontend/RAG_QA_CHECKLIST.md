# RAG QA Checklist

Phase 14 暂未修改移动端 UI。当前 RAG 主要用于后端 API 和 Agent workflow 内部增强。

## Backend API QA

- [ ] `POST /api/v1/rag/search` 在 `RAG_ENABLED=false` 时返回 `rag_enabled=false`。
- [ ] `POST /api/v1/rag/search` 在 `RAG_ENABLED=true` 时只返回 safe excerpt 和 citation。
- [ ] 本人搜索本人数据可返回结果。
- [ ] 家庭成员搜索目标成员数据必须提供 `family_id`。
- [ ] 权限不足时返回统一 403。
- [ ] response 不包含 `raw_text`、`symptom_text`、`raw_extracted_text`、`file_path`、token、password、API key、traceback、SQL。

## Agent QA

- [ ] 默认 `RAG_ENABLED=false` 时 `daily_health_brief` 行为不变。
- [ ] `RAG_ENABLED=true` 时 `daily_health_brief` 可追加系统内 citation。
- [ ] RAG 失败时 `daily_health_brief` 仍 completed，并回退原规则简报。
- [ ] `medical_event_draft_create` 只使用 safe `structured_hints.rag_sources`。
- [ ] RAG 不创建正式 `medical_event`。
- [ ] RAG 不写正式健康事实。

## Mobile QA

移动端暂不新增 RAG 页面。后续如展示 RAG citation，需要继续遵守：

- 只展示来源摘要和 citation。
- 不展示文件路径。
- 不展示 OCR 原文全文。
- 不展示 token/password/API key。
- 不把 RAG citation 表达成诊断结论。
