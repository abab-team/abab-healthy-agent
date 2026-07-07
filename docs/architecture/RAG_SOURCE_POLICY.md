# Phase 14 RAG Source Policy

## Source of Truth

RAG 的 source policy 位于：

- `backend/app/rag/source_policy.py`
- `backend/app/rag/schemas.py`
- `backend/app/rag/index_builder.py`

## 可索引来源

只允许索引项目内部数据的安全摘要，不允许外部医学知识库。

## 必须脱敏或禁止

RAG source、chunk、API response、Agent trace/debug 中不得包含：

- `raw_text`
- `symptom_text`
- `raw_extracted_text`
- `file_path`
- 本机路径
- API key / token / password / private key
- traceback / SQL
- raw prompt
- raw LLM response

## 返回策略

RAG API 只返回 `safe_excerpt` 和 `citation`，不返回完整正文，不做医学答案生成。

## 失败策略

- RAG 关闭：返回 `rag_enabled=false` 和 `fallback_reason=rag_disabled`。
- 权限不足：API 返回统一 403；Agent workflow 内部降级，不返回目标数据。
- 检索失败：Agent workflow 回退到无 RAG 的原行为。
