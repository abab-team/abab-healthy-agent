# Phase 08 Scope Reconciliation

本文档用于整理原计划 Phase 08: Agent Tools 与当前 Phase 07 实际实现之间的重叠，避免后续重复实现或误判 Phase 08 已完成。

## 原计划 Phase 08 目标

`CODEX_IMPLEMENTATION_PLAN.md` 中原计划 Phase 08 的目标是把业务 service 包装成受控 Agent tools，并确保：

- Tool 只能接收 runtime 确定的 `target_user_id`。
- Tool input 不允许自由携带 `current_user_id` 或 `target_user_id`。
- Tool 不直接创建数据库 session。
- Tool 不绕过 service。
- 写入 Tool 必须经过 Harness / Tool Caller / Tool Executor 门禁。
- 权限不足时不得调用底层 service。
- 工具调用必须可追踪。

## Phase 07 已完成的 Phase 08 相关能力

Phase 07 为了完成 Agent 层闭环，已经提前覆盖了部分原 Phase 08 能力：

- Tool Registry。
- Tool Metadata。
- Tool Base。
- Tool Executor。
- confirmation / permission / safety gate。
- `agent_tool_calls` 基础记录。
- 只读健康 tools：
  - `health_profile.get`
  - `health_data.blood_pressure.summary`
  - `health_record.symptoms.summary`
  - `medical_timeline.followups.list`
  - `alerts.active.list`
- 写入类 draft tools：
  - `health_record.symptom_draft.create`
  - `document_processing.medical_event_draft.create`
  - `alerts.create`
- `daily_health_brief` 确定性 workflow 通过 Tool Executor 调用只读 tools。

## Phase 08 仍需补齐或收口的能力

Phase 08 不能直接视为完成。建议在 Phase 08 正式执行以下工作：

- 对原计划工具清单做 gap review。
- 梳理已经存在但仍是占位或未注册的 tool 文件。
- 判断是否需要补齐：
  - `resolve_family_member`
  - `check_member_permission`
  - `get_recent_metrics`
  - `get_recent_blood_pressure`
  - `get_symptom_records`
  - `get_medical_events`
  - `get_medical_documents`
  - `get_latest_daily_report`
  - `get_active_alerts`
  - `create_symptom_record_draft`
  - `save_symptom_record_from_draft`
  - `extract_document_summary`
  - `save_medical_event_from_document`
  - `generate_daily_report`
- 明确哪些工具在当前医疗安全边界内应继续保持未实现。
- 整理每个 tool 的 permission type、permission action、risk level、confirmation 要求和输出脱敏规则。
- 记录 schema 风险，例如 `alerts:create` 当前仍是临时权限桥接。
- 为后续 Agent API 最小入口准备稳定的 request / result / tool contract。

## Phase 08 当前不应该做的能力

Phase 08 只做 Agent Tools 补齐与收口，不应提前实现：

- LLM Client。
- LangGraph。
- RAG。
- OCR / upload。
- Web 前端或移动端。
- Agent API。
- 新 migration / models。
- 诊断、处方、剂量、停药建议。

## 建议 Phase 08 正式范围

建议 Phase 08 命名为：Agent Tools 补齐与收口。

建议拆分：

1. Agent Tools gap review。
2. 必要工具补齐。
3. 工具权限与 schema 风险整理。
4. 工具输出安全与脱敏验收。
5. 为 Agent API 最小入口准备契约，但不实现 Agent API。

Phase 08 完成标准应以“工具边界稳定、缺口清晰、权限声明明确、可安全接入 Agent API”为准，而不是引入 LLM 或 LangGraph。
