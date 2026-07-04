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
