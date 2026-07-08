# LangGraph Orchestration Design

Phase 17 引入可选图编排适配层，用于后续逐步把 Agent workflow 从线性编排迁移到 LangGraph 风格节点。

## 当前范围

当前只接入：

- `chat` / `chat_workflow`

当前不接入：

- `symptom_draft_create`
- `medical_event_draft_create`
- `alert_create`
- 其他 workflow

`daily_health_brief` 仅保留配置开关与设计说明，默认不启用。

## 默认配置

```text
LANGGRAPH_ENABLED=false
LANGGRAPH_CHAT_QUERY_ENABLED=false
LANGGRAPH_DAILY_BRIEF_ENABLED=false
LANGGRAPH_TRACE_NODE_SUMMARY=true
```

默认关闭时，Phase 16 的 deterministic chat workflow 行为不变。

## 节点摘要

开启 chat graph 后，系统会记录安全节点摘要：

```text
input_safety > parse_intent > permission_gate > tool_execution > compose_answer > output_safety
```

节点摘要写入 `agent_safety_checks` 的安全摘要字段，用于 Agent Run 详情页展示。

## 安全边界

Graph adapter 不负责：

- 查询数据库
- 调用 tools
- 写业务数据
- 判断用户身份
- 决定 `current_user_id` / `family_id` / `target_user_id`
- 绕过 Agent Runtime safety
- 绕过 Tool Executor permission / confirmation

Graph state 禁止包含：

- `raw_text`
- `symptom_text`
- `raw_extracted_text`
- `file_path`
- `raw_prompt`
- `raw_llm_response`
- `tool_name`
- `input_data`
- token / password / API key / private key
- traceback / SQL / 本机路径

## Fallback

本阶段图编排层是薄 adapter。默认关闭时不参与执行；开启后仍调用现有 deterministic runner。

如果后续接入真实 LangGraph runtime，必须继续保持：

- graph 失败 fallback 到现有 deterministic workflow。
- fallback 不影响默认 smoke。
- trace/debug 不记录敏感 state。
- 不开放通用 tool execution。

## 非目标

- 不新增 migration / model。
- 不新增业务 API。
- 不接真实 LLM 决策。
- 不实现通用 LangGraph agent。
- 不改变写入 workflow 边界。
