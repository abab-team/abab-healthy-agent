# Phase 11 LLM Provider Verification

Phase 11 用于收口真实 provider smoke、daily_health_brief LLM 输出质量评估，以及安全、fallback、trace/debug、成本与稳定性风险说明。

## 已完成内容

- 新增 `scripts/smoke/llm_provider_smoke.py` 与 PowerShell 包装脚本。
- 新增 `backend/tests/evaluation/test_daily_brief_llm_quality.py`。
- 新增 `scripts/smoke/daily_brief_llm_quality_smoke.py` 与 PowerShell 包装脚本。
- 新增真实 provider runbook 与 daily brief evaluation 文档。

## 仍保持的边界

- 默认 `LLM_ENABLED=false`。
- 默认 `LLM_PROVIDER=mock`。
- 默认 `DAILY_BRIEF_USE_LLM=false`。
- 真实 provider smoke 只有显式设置 `LLM_REAL_SMOKE_ENABLED=true` 才会运行。
- 当前只有 `daily_health_brief` 可选使用 LLM。
- `symptom_draft_create`、`medical_event_draft_create`、`alert_create` 和其他 workflow 尚未接入 LLM。
- LLM 不直接查数据库、不调用 tool、不写业务数据。
- LLM 不决定 `current_user_id`、`family_id`、`target_user_id`。
- 不实现 Auth/JWT、LangGraph、OCR/RAG。

## 成本、延迟与稳定性风险

真实 provider 会引入：

- 网络延迟与超时。
- provider 不可用或限流。
- token 成本。
- 输出质量波动。
- 模型版本漂移。

因此真实 provider 仍必须受配置开关控制，并保留规则简报 fallback。真实 provider 在线 smoke 通过也不等于生产可用，需要后续结合部署、监控、速率限制、审计与 Auth/JWT 再做产品化评估。

## 安全记录策略

允许记录：

- `llm_used`
- `llm_provider`
- `llm_model`
- `fallback_used`
- `fallback_reason`
- `safety_filtered`

禁止记录：

- API key
- raw prompt
- raw LLM response
- raw_text
- symptom_text
- raw_extracted_text
- file_path
- token/password/key
- traceback
- SQL
- 本机敏感路径

## Phase 11 关闭条件

- mock provider smoke 通过。
- 未配置真实 provider 时安全 skip。
- daily brief evaluation harness 通过 mock 用例。
- mobile backend smoke 默认配置不受影响。
- 文档说明真实 provider 配置、安全边界、质量评估、成本/延迟/稳定性风险。
- 没有提交 `.env`、API key、真实 provider 原始输出或用户附件。
