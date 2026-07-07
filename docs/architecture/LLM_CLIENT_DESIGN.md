# LLM Client Design

本文档记录 Phase 10.A 的 LLM Client 最小封装设计。

## 目标

Phase 10.A 只新增后端 LLM 底座，为后续 Agent workflow 可选接入 LLM 做准备。

本阶段不接入 `daily_health_brief`，不修改 Agent workflow，不调用 tools，不查数据库，不写业务数据。

## Provider

当前支持：

- `mock`：默认 provider，不请求外部网络，返回稳定文本，用于测试和本地开发。
- `openai_compatible`：OpenAI-compatible chat completions 适配器。

默认配置：

```text
LLM_ENABLED=false
LLM_PROVIDER=mock
```

真实 provider 需要显式配置：

```text
LLM_ENABLED=true
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=<provider base url>
LLM_API_KEY=
LLM_MODEL=<model name>
```

真实密钥只能写入本地 `.env` 或部署环境变量，不能写入仓库。

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

## 错误处理

错误类型：

- `LLMConfigurationError`
- `LLMProviderError`
- `LLMTimeoutError`

错误信息不得泄露 API key、完整敏感请求、traceback、SQL 或本机路径。
