# LLM Client Design

本文档记录 Phase 10.A 的 LLM Client 最小封装，以及 Phase 10.B 对 `daily_health_brief` 的可选接入设计。

## 目标

Phase 10.A 只新增后端 LLM 底座，为后续 Agent workflow 可选接入 LLM 做准备。

Phase 10.B 只把 LLM Client 可选接入 `daily_health_brief`。默认不启用 LLM，不接入其他 workflow，不调用 LangGraph/OCR/RAG。

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
- LLM 输出被 Safety Policy 拦截。

fallback 不应让 Agent API 失败，除非规则简报本身失败。

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

Phase 10.B 中，`daily_health_brief` 的 LLM 输出会先经过 output safety 检查；不安全时回退规则简报。Runtime 仍会对最终输出再执行一次 output safety。

## 错误处理

错误类型：

- `LLMConfigurationError`
- `LLMProviderError`
- `LLMTimeoutError`

错误信息不得泄露 API key、完整敏感请求、traceback、SQL 或本机路径。
