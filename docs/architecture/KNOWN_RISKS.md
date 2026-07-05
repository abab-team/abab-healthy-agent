# 已知工程风险

本文档记录当前阶段明确保留、但不在本阶段修改数据库结构或业务模型的风险。

## Phase 06.A 记录

1. `daily_reports` 当前唯一约束为 `user_id + report_date`。
   - 现阶段 family report API 会继续按 `family_id` 尽量限定查询范围。
   - 如果未来需要支持同一用户在 personal report、不同 family context 下保存多份同日报告，需要单独进行 schema review 并创建 migration。
   - Phase 06.A 不修改该约束。

2. `health_metrics` 与 `blood_pressure_records` 当前没有 `family_id` 字段。
   - 现阶段策略是：这些数据作为 user-owned health facts 保存，family member API 必须先通过家庭权限检查后才能访问。
   - 如果未来需要按家庭上下文隔离同一用户的 metrics / blood pressure 数据，需要单独进行 schema review 并创建 migration。
   - Phase 06.A 不新增字段、不修改 migration。

## Phase 07 Closeout 记录

1. `alerts:create` 临时权限桥接已在 Phase 08.A 收口。
   - Phase 07.G 曾临时将 `alerts:create` 在 Tool Executor 权限入口窄映射到 `alerts:view`。
   - Phase 08.A 已新增独立 `member_share_permissions.can_create_alerts` 字段和 migration。
   - Tool metadata 继续声明 `alerts:create`，Permissions policy 现在映射到 `can_create_alerts`。
   - Tool Executor 已移除 `alerts:create -> alerts:view` 临时桥接。
   - 后续风险降级为兼容性观察：任何新 alert 写入入口都必须显式使用 `alerts:create`，不得重新依赖 `alerts:view`。

2. `health_metrics` 与 `blood_pressure_records` 仍没有 `family_id` 字段。
   - 当前策略仍是 user-owned facts + family permission access。
   - family 访问必须先经过 family_id 与 permission check，但数据事实本身不按 family context 分表或隔离。
   - 如果未来需要同一用户在不同 family context 下隔离指标数据，需要单独 schema review 与 migration。
   - 本阶段只记录风险，不修改 models 或 migration。

3. `daily_reports` 当前唯一约束仍为 `user_id + report_date`。
   - 当前不能在同一用户、同一天、不同 family context 下保存多份独立 daily report。
   - 如果未来需要 family context daily report，需要单独 schema review 与 migration。
   - 本阶段只记录风险，不修改 models 或 migration。

## Phase 08 Closeout 记录

1. Demo Header Auth 风险。
   - 当前 API 仍使用 `X-Current-User-Id` 作为开发调试身份入口。
   - Phase 09 前端 MVP 可以使用 demo 用户切换页验证产品闭环，但必须明确标注为开发调试模式。
   - 该机制不能用于生产环境，真实 Auth/JWT 需要在后续 Phase 15 或外部试用前单独收口。

2. 前端阶段风险。
   - Phase 09 目标是可用前端 / 调试页面，不是商业级完整 UI。
   - 前端不得开放通用 tool execution，不得允许用户直接输入任意 `tool_name` / `input_data`。
   - 前端必须明确区分 pending draft 与正式健康事实，并展示 confirmation 边界。

3. LLM 后移风险。
   - Phase 09 优先做前端闭环，LLM Client 后移到 Phase 10。
   - 在 LLM 接入前，Agent 输出继续以确定性 workflow 和安全策略为准。
   - 后续 LLM 接入不得绕过 Safety Policy、Tool Executor、权限、confirmation 和 trace。
