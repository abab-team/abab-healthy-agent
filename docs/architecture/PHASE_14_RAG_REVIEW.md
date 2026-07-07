# Phase 14 RAG Review Notes

## 结论

Phase 14 新增内部 RAG 检索地基、受控 `/api/v1/rag/search` API、daily_health_brief citation 增强，以及 medical_event_draft_create 的安全 hints 增强。

## 完成内容

- 新增 `backend/app/rag/**`。
- 新增 RAG source policy。
- 新增安全 chunking。
- 新增 simple retrieval provider。
- 新增动态内部索引构建。
- 新增 `POST /api/v1/rag/search`。
- `daily_health_brief` 在 `RAG_ENABLED=true` 时追加安全 citation。
- `medical_event_draft_create` 在 `RAG_ENABLED=true` 时追加安全 `structured_hints.rag_sources`。
- 新增 RAG tests、evaluation tests、API tests。
- 新增 RAG smoke scripts。

## 保持边界

- 未新增 migration/model。
- 未接入真实 embedding provider。
- 未接入 vector DB。
- 未接入外部医学知识库。
- 未实现 RAG chatbot。
- 未修改移动端。
- 未开放通用 tool execution。
- 未允许 `tool_name` / `input_data`。
- 未让 RAG 写入正式健康事实。

## 后续建议

下一阶段如继续推进，建议进入 Phase 15：RAG 检索质量、真实索引持久化与权限审计增强。

该阶段前必须先 review 是否需要持久化 RAG index、embedding provider、vector DB、索引刷新策略和数据删除/撤权同步策略。
