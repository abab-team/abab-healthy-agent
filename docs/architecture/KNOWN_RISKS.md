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

1. `alerts:create` 当前是临时权限桥接。
   - Phase 07.G 引入 `alerts.create` Agent tool，用于在用户确认后创建提醒。
   - 当前权限模型已有 `alerts:view`，但没有专门的 `can_create_alerts` 或 `alerts:create` 权限字段。
   - 现阶段只在 Tool Executor 权限入口做窄映射：tool metadata 仍声明 `alerts:create`，实际检查临时映射到 `alerts:view` 加 family membership。
   - 该映射不得污染其他 permission_type，也不得扩散到 API 层、service 层或模型层。
   - 后续 Phase 08 或 schema review 需要评估是否增加专门 `can_create_alerts` 或 `alerts:create` 权限字段，并通过 migration 显式落地。
   - 本阶段只记录风险，不修改 models 或 migration。

2. `health_metrics` 与 `blood_pressure_records` 仍没有 `family_id` 字段。
   - 当前策略仍是 user-owned facts + family permission access。
   - family 访问必须先经过 family_id 与 permission check，但数据事实本身不按 family context 分表或隔离。
   - 如果未来需要同一用户在不同 family context 下隔离指标数据，需要单独 schema review 与 migration。
   - 本阶段只记录风险，不修改 models 或 migration。

3. `daily_reports` 当前唯一约束仍为 `user_id + report_date`。
   - 当前不能在同一用户、同一天、不同 family context 下保存多份独立 daily report。
   - 如果未来需要 family context daily report，需要单独 schema review 与 migration。
   - 本阶段只记录风险，不修改 models 或 migration。
