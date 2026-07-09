# LLM Client Design

## Phase 21 Reflection / Critic Supplement

Phase 21 adds an answer critic layer after draft answer composition and before final output safety.

- Rule critic is enabled by default with `RULE_CRITIC_ENABLED=true`.
- Optional LLM critic is disabled by default with `LLM_CRITIC_ENABLED=false`.
- The critic receives only a user-question excerpt, a safe tool-result summary, and the draft answer.
- The critic must not receive raw OCR, file paths, raw prompts, raw LLM responses, token/key/password values, traceback, SQL, or full sensitive health text.
- The critic does not query DB, call tools, write business data, decide user/family identity, or override permissions.
- If review fails, a safe rewrite is used and then final output safety still runs.

## Phase 22 Stateful LangGraph Supplement

Phase 22 keeps LangGraph optional and disabled by default while adding a stateful graph pipeline for `chat_workflow`.

- `LANGGRAPH_ENABLED=false`, `LANGGRAPH_CHAT_QUERY_ENABLED=false`, and `LANGGRAPH_STRICT_MODE=false` by default.
- Graph state stores only safe summaries: node names, intent label, plan status, permission delegation status, tool result counts, critic summary, final answer excerpt, and fallback reason.
- Graph state must not store raw prompt, raw LLM response, token/key/password, file path, OCR full text, SQL, traceback, `tool_name`, or `input_data`.
- Tool execution remains delegated to the existing workflow and ToolExecutor. LangGraph does not call tools directly.
- If graph orchestration fails and strict mode is off, the workflow falls back to the deterministic runner.

## Phase 20 Prompt Registry 与 Planner 补充

Phase 20 在 LLM Client 底座之上新增版本化 Prompt Registry 与受控 LLM Planner。

- `backend/app/agent/prompts/registry.py` 统一登记 planner、answer composer、memory extractor、critic prompt。
- 每个 prompt 记录 `name`、`version`、`input_schema`、`output_schema`、`safety_notes`、`allowed_intents` 与 `created_at`。
- `LLM_PLANNER_ENABLED=false` 为默认值；关闭时 `chat` workflow 仍完全使用规则解析。
- 仅当规则解析为 unknown 且 `LLM_PLANNER_ENABLED=true` 时，planner 才会请求 LLM 生成 JSON plan。
- LLM 输出不得包含 `tool_name`、`input_data`、用户 ID、family ID、SQL 或文件路径。
- `PlanValidator` 校验 intent、metric_type、member_scope、time_range、aggregation、confidence 与 clarification 状态。
- 工具选择由系统白名单映射完成，仍走 ToolExecutor / Permission / Safety / Trace。
- `LLM_ANSWER_COMPOSER_ENABLED=false` 为默认值；开启后也只允许润色安全摘要，输出必须经过 SafetyPolicy。

本文档记录 Phase 10.A 的 LLM Client 最小封装、Phase 10.B 对 `daily_health_brief` 的可选接入设计，以及 Phase 10.C 的 LLM 输出安全与 fallback 收口。

## 目标

Phase 10.A 只新增后端 LLM 底座，为后续 Agent workflow 可选接入 LLM 做准备。

Phase 10.B 只把 LLM Client 可选接入 `daily_health_brief`。默认不启用 LLM，不接入其他 workflow，不调用 LangGraph/OCR/RAG。

Phase 10.C 只强化 `daily_health_brief` 的 LLM prompt、安全输出、fallback、trace/debug 摘要和测试覆盖，不新增业务能力，不做真实在线 LLM smoke。

## Provider

当前支持：

- `mock`：默认 provider，不请求外部网络，返回稳定文本，用于测试和本地开发。
- `openai_compatible`：OpenAI-compatible chat completions 适配器。

默认配置：

```text
LLM_ENABLED=false
LLM_PROVIDER=mock
DAILY_BRIEF_USE_LLM=false
```

真实 provider 需要显式配置：

```text
LLM_ENABLED=true
DAILY_BRIEF_USE_LLM=true
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=<provider base url>
LLM_API_KEY=
LLM_MODEL=<model name>
```

真实密钥只能写入本地 `.env` 或部署环境变量，不能写入仓库。

## daily_health_brief 可选接入

启用条件必须同时满足：

```text
LLM_ENABLED=true
DAILY_BRIEF_USE_LLM=true
```

默认配置下，`daily_health_brief` 继续使用规则简报，不需要外部 API key。

LLM 输入只包含只读 Agent tools 已整理后的结构化摘要：

- 健康档案摘要。
- 血压记录数量与最近记录时间。
- 症状记录数量与安全摘录。
- 待随访事件数量。
- active reminders 数量。

LLM 输入不得包含：

- `raw_text`
- `file_path`
- `raw_extracted_text`
- API key
- 原始 prompt 之外的敏感原文

## Fallback 策略

以下情况必须回退到规则简报：

- `LLM_ENABLED=false`
- `DAILY_BRIEF_USE_LLM=false`
- LLM 配置错误。
- LLM provider 调用失败或超时。
- LLM 返回空内容。
- LLM response schema 不完整。
- LLM 输出被 Safety Policy 拦截。

fallback 不应让 Agent API 失败，除非规则简报本身失败。

Phase 10.C 将 fallback reason 收口为短枚举式安全摘要，例如：

- `llm_disabled`
- `daily_brief_use_llm_disabled`
- `llm_configuration_error`
- `llm_provider_error`
- `llm_timeout`
- `empty_llm_output`
- `llm_response_invalid`
- `llm_output_safety_blocked`

这些 reason 不包含 API key、raw prompt、raw response、traceback、SQL、本机路径或健康原文。

## Prompt 与输出安全

`daily_health_brief` 的 LLM system prompt 必须明确：

- 只根据系统内结构化记录整理健康简报。
- 不替代医生。
- 不做诊断、确诊、处方、剂量建议、停药或换药建议。
- 不判断正常/异常/高风险/低风险。
- 不承诺急救、报警或自动联系医院/家人。
- 如遇紧急情况，应联系医生或当地急救服务。

user prompt 只能包含只读 tools 输出后的结构化摘要，不得包含：

- `raw_text`
- `symptom_text`
- `raw_extracted_text`
- `file_path`
- 原始长文本
- API key / token / password
- traceback / SQL / 本机路径

LLM 输出如包含诊断、确诊、处方、剂量、停药、自动急救、自动报警、自动联系医院/家人、不用就医、一定没事、正常/异常、高风险/低风险等内容，必须回退到规则简报。unsafe LLM 原文不得返回给用户，也不得写入 trace/debug。

Phase 10.C 会在 LLM 分支尝试后记录安全摘要到 `agent_safety_checks`，但只记录 `llm_used`、`fallback_used`、`fallback_reason`、`safety_filtered` 等摘要，不记录 prompt 全文或 LLM 原始响应。

## Client API

统一入口：

- `get_llm_client(settings)`
- `LLMClient.generate_text(...)`
- `LLMClient.chat(...)`

输出包含：

- `content`
- `provider`
- `model`
- `usage`
- `finish_reason`
- `is_mock`
- `error`

## 安全边界

LLM Client 是底层文本生成适配层，不能绕过 Agent Safety。

LLM Client 不负责：

- 查询数据库。
- 调用 Agent Tool。
- 写入业务数据。
- 判断病情。
- 生成诊断、处方、剂量或停药建议。
- 急救判断。

未来业务接入时，LLM 输出必须经过 Safety Policy，并继续遵守权限、confirmation、trace 和 Tool Executor 边界。

Phase 10.B/10.C 中，`daily_health_brief` 的 LLM 输出会先经过 output safety 检查；不安全时回退规则简报。Runtime 仍会对最终输出再执行一次 output safety。

当前只有 `daily_health_brief` 可选使用 LLM。`symptom_draft_create`、`medical_event_draft_create`、`alert_create` 和其他 workflow 尚未接入 LLM。

## 错误处理

错误类型：

- `LLMConfigurationError`
- `LLMProviderError`
- `LLMTimeoutError`

错误信息不得泄露 API key、完整敏感请求、traceback、SQL 或本机路径。
## Phase 11 Provider Verification

Phase 11 在不新增业务能力的前提下补齐真实 provider 验证路径与 daily_health_brief 质量评估：

- `scripts/smoke/llm_provider_smoke.ps1`：默认 mock provider，不联网；真实 provider 必须显式设置 `LLM_REAL_SMOKE_ENABLED=true`。
- `scripts/smoke/daily_brief_llm_quality_smoke.ps1`：使用合成结构化摘要评估 daily brief 输出质量。
- `backend/tests/evaluation/test_daily_brief_llm_quality.py`：覆盖 normal、empty、multi-member、follow-up reminder、safety-sensitive 五类合成用例。
- 真实 provider 未配置 `LLM_API_KEY` 时输出安全 skip，不失败也不伪装在线通过。
- smoke 与评估输出只包含 provider、model、is_mock、status、latency、content_length 或 failed_checks，不输出 raw prompt 或 raw response。
- 真实 provider 会带来成本、延迟、限流、稳定性和模型漂移风险，因此仍必须保留规则简报 fallback。

Phase 11 后仍保持：只有 `daily_health_brief` 可选接入 LLM；其他 workflow 未接入 LLM；LLM 不查 DB、不调用 tool、不写数据。
