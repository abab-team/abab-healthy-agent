# LLM Real Provider Smoke Runbook

本文档记录 Phase 11.A 的真实 LLM provider 受控 smoke 路径。该路径用于验证 OpenAI-compatible provider 的最小连通性，不代表生产能力已经开放。

## 默认行为

- 默认只运行 `mock` provider。
- 默认不请求外部网络。
- 默认不需要真实 API key。
- 未显式开启 `LLM_REAL_SMOKE_ENABLED=true` 时，不会调用真实 provider。

## 安全开启真实 Provider Smoke

真实 provider smoke 只允许在本地 `.env` 或临时 shell 环境变量中配置：

```text
LLM_REAL_SMOKE_ENABLED=true
LLM_ENABLED=true
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=<provider base url>
LLM_API_KEY=<local secret only>
LLM_MODEL=<model name>
LLM_TIMEOUT_SECONDS=30
```

不要把 `.env`、真实 `LLM_API_KEY`、真实 provider 输出日志提交到仓库。

## 运行命令

默认 mock smoke：

```powershell
scripts/smoke/llm_provider_smoke.ps1
```

真实 provider smoke：

```powershell
$env:LLM_REAL_SMOKE_ENABLED="true"
$env:LLM_ENABLED="true"
$env:LLM_PROVIDER="openai_compatible"
$env:LLM_BASE_URL="https://example-compatible-endpoint/v1"
$env:LLM_API_KEY="<local secret only>"
$env:LLM_MODEL="<model>"
scripts/smoke/llm_provider_smoke.ps1
```

## 输出边界

smoke 输出只允许包含：

- `STATUS`
- `PROVIDER`
- `MODEL`
- `IS_MOCK`
- `LATENCY_MS`
- `CONTENT_LENGTH`

smoke 输出不得包含：

- API key
- raw prompt
- 完整 LLM response
- 真实用户健康数据
- traceback
- SQL
- 本机敏感路径

## 未配置真实 Key 时的行为

如果 `LLM_REAL_SMOKE_ENABLED=true` 但缺少 `LLM_API_KEY`，脚本会输出：

```text
STATUS=SKIPPED_REAL_PROVIDER_SMOKE
REASON=missing_llm_api_key
```

这表示真实 provider smoke 被安全跳过，不表示真实 provider 已在线通过。

## Phase 11 边界

Phase 11 只验证 provider smoke 路径与安全开关：

- 不修改前端。
- 不新增业务 API。
- 不新增 migration/model。
- 不接入其他 workflow。
- 不开放通用 tool execution。
- 不实现 Auth/JWT、LangGraph、OCR/RAG。
