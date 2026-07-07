# Phase 10 LLM Safety Notes

本文档记录 Phase 10.C 对 `daily_health_brief` 可选 LLM 接入的安全收口结果。

## 当前范围

- 当前只有 `daily_health_brief` 可选使用 LLM。
- 默认 `LLM_ENABLED=false`。
- 默认 `DAILY_BRIEF_USE_LLM=false`。
- 默认仍使用规则简报，不需要真实 API key。
- `symptom_draft_create`、`medical_event_draft_create`、`alert_create` 和其他 workflow 尚未接入 LLM。
- 本阶段不做真实在线 LLM smoke。

## Prompt 边界

system prompt 必须明确：

- 只根据系统内结构化记录整理健康简报。
- 不替代医生。
- 不做诊断或确诊。
- 不给处方。
- 不给药物剂量建议。
- 不建议停药或换药。
- 不判断正常、异常、高风险或低风险。
- 不承诺急救、报警或自动联系医院/家人。
- 如遇紧急情况，应联系医生或当地急救服务。

user prompt 只能包含只读 Agent tools 汇总后的结构化摘要，不得包含：

- `raw_text`
- `symptom_text`
- `raw_extracted_text`
- `file_path`
- 原始长文本
- API key、token、password
- traceback
- SQL
- 本机路径

## 输出安全

LLM 输出如包含以下内容，必须 fallback 到规则简报：

- 诊断、确诊。
- 处方。
- 剂量建议。
- 停药、换药建议。
- 自动急救、自动报警、自动联系医院、自动联系家人。
- 不用就医、一定没事。
- 正常、异常、高风险、低风险等医学判断。

unsafe LLM 原文不得返回给用户，也不得写入 trace/debug。

## Fallback

以下情况均 fallback 到规则简报：

- `LLM_ENABLED=false`
- `DAILY_BRIEF_USE_LLM=false`
- provider 配置错误。
- provider 抛异常。
- provider timeout。
- provider 返回空内容。
- provider 返回 unsafe 内容。
- LLM response schema 不完整。

fallback reason 只允许记录短安全摘要，例如：

- `llm_disabled`
- `daily_brief_use_llm_disabled`
- `llm_configuration_error`
- `llm_provider_error`
- `llm_timeout`
- `empty_llm_output`
- `llm_response_invalid`
- `llm_output_safety_blocked`

## Trace / Debug

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
- `raw_text`
- `symptom_text`
- `raw_extracted_text`
- `file_path`
- token / password / private key
- traceback
- SQL
- 本机路径

## 后续 Review

Phase 10 Batch Review 需要复核：

- 默认 smoke 不因 LLM 接入变化而失败。
- 真实 provider 尚未在线 smoke 的风险是否仍准确记录。
- 后续任何新增 LLM workflow 是否重新经过 prompt、权限、Tool Executor、Safety Policy、trace/debug 与 fallback review。
