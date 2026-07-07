# Phase 14 RAG Design

## 定位

Phase 14 的 RAG 只检索家庭健康系统内部已有记录的安全摘要，用于“根据系统内记录”补充上下文和 citation。它不是通用医学问答，不接入外部医学知识库，不生成诊断、处方、剂量、停药建议，也不替代医生判断。

## 默认配置

- `RAG_ENABLED=false`
- `RAG_PROVIDER=simple`
- `RAG_INDEX_INTERNAL_SOURCES=true`
- `RAG_ALLOW_EXTERNAL_KNOWLEDGE=false`
- `RAG_MAX_CHUNK_CHARS=1200`
- `RAG_TOP_K=5`
- `RAG_STORE_RAW_TEXT=false`
- `RAG_EMBEDDING_PROVIDER=mock`
- `RAG_RETRIEVAL_PROVIDER=simple`
- `RAG_MIN_SCORE=0.0`

默认关闭 RAG。开启后也只使用内部安全摘要和简单检索，不调用真实 embedding 服务，不使用 vector DB。

## 数据边界

允许进入 RAG 的内容必须是安全摘要：

- health profile summary
- blood pressure summary
- symptom record summary
- medical event summary
- medical event draft summary
- medical document metadata
- document extraction preview
- OCR extraction preview
- daily report summary
- alert summary
- agent generated brief summary

禁止进入 RAG：

- 完整 `raw_text`
- 完整 `symptom_text`
- 完整 `raw_extracted_text`
- 上传文件全文
- `file_path` 或本机路径
- token / password / API key / private key
- traceback / SQL
- raw prompt
- 完整 LLM 原始响应

## 权限模型

RAG 检索必须使用当前用户身份和目标用户身份：

- 本人检索本人数据：允许。
- 家庭成员检索目标成员数据：必须提供 `family_id`，并按 source type 映射到对应 family share permission。
- 权限不足：不返回目标数据，不泄露目标数据是否存在。

权限映射：

| RAG source type | permission |
| --- | --- |
| `health_profile_summary` | `profile:view` |
| `blood_pressure_summary` | `metrics:view` |
| `symptom_record_summary` | `symptoms:view` |
| `medical_event_summary` | `medical_events:view` |
| `medical_event_draft_summary` | `medical_events:view` |
| `medical_document_metadata` | `documents:view` |
| `document_extraction_preview` | `documents:view` |
| `ocr_extraction_preview` | `documents:view` |
| `daily_report_summary` | `reports:view` |
| `alert_summary` | `alerts:view` |
| `agent_generated_brief_summary` | `memory_summary:view` |

## API

新增受控 API：

- `POST /api/v1/rag/search`

该接口只返回 query、target_user_id、family_id、result_count、rag_enabled、fallback_reason 和 results。results 仅包含 source type、source id、title、safe excerpt、citation、score、permission type 与安全 metadata。

该接口不生成医学回答，也不返回 raw content、文件路径、密钥或调试堆栈。

## Agent 接入

Phase 14 只允许两个窄接入：

- `daily_health_brief`：RAG 开启时追加内部 citation 摘要；关闭或失败时回退到原规则简报。
- `medical_event_draft_create`：RAG 开启时向工具输入追加安全 `structured_hints.rag_sources`；关闭或失败时不影响原流程。

未接入 `symptom_draft_create`、`alert_create`、通用 tool execution、LangGraph、外部医学知识库、真实 embedding 或 vector DB。

## Safety

RAG 结果只作为上下文和 citation，不允许直接产生医学判断。任何后续 LLM 输出仍必须经过 Agent Safety Policy。
