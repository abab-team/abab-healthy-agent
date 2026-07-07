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

## Phase 09 Final Review 记录

1. 移动端 MVP 不是生产发布包。
   - Phase 09.4 完成的是 Expo + React Native MVP 演示闭环。
   - 真实 Auth/JWT、生产部署、发布包、隐私合规与真实用户账号仍未完成。
   - 当前仍使用 `X-Current-User-Id` demo header。

2. 真机视觉 QA 仍需要用户手动完成。
   - Codex 已验证 Web export 与 Web HTTP 200。
   - Expo Go 真机扫码、不同屏幕尺寸、中文换行和触控体验需要用户按 QA checklist 手动确认。

3. 草稿正式确认入库仍未接入移动端。
   - `symptom_draft_create` 与 `medical_event_draft_create` 只创建待确认草稿。
   - `drafts` 页面仍为 mock，不执行正式 `symptom_record` 或 `medical_event` 确认入库。
   - 后续实现正式确认入库前必须再次 review 权限、确认语义和审计。

4. PostgreSQL / Docker 完整复验仍受本机环境影响。
   - Phase 09 smoke 使用临时 SQLite demo DB 完成。
   - Docker Desktop engine 可用后仍建议补跑 PostgreSQL / docker-compose 路径。

## Phase 10.A 记录

1. LLM Client 尚未接入业务 workflow。
   - Phase 10.A 只新增底层 client，不改变 `daily_health_brief` 或任何 Agent workflow 行为。
   - 后续接入前必须单独 review prompt、Safety Policy、trace、权限与 fallback 策略。

2. 真实 provider 配置风险。
   - 默认 `LLM_ENABLED=false`，默认 provider 为 `mock`。
   - `openai_compatible` 需要从本地 `.env` 或部署环境变量读取 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`。
   - API key 不得写入代码、文档示例或测试输出。

3. LLM 输出安全风险。
   - LLM Client 只负责文本生成，不判断病情、不生成诊断、处方、剂量或停药建议。
   - 后续任何业务接入必须经过 Agent Safety Policy。
   - LLM 不能决定 `current_user_id`、`family_id`、`target_user_id`，不能直接调用 tool，不能直接写业务数据。

## Phase 10.B 记录

1. `daily_health_brief` LLM 接入默认关闭。
   - 必须同时设置 `LLM_ENABLED=true` 与 `DAILY_BRIEF_USE_LLM=true` 才会尝试调用 LLM。
   - 默认 smoke 和默认 API 行为仍使用规则简报。

2. LLM brief fallback 风险。
   - provider 配置错误、超时、失败、空输出或 safety blocked 会回退规则简报。
   - fallback 原因只作为安全摘要记录，不记录 API key、原始 prompt 全文或完整 LLM 原始响应。

3. LLM 输入边界风险。
   - 当前只传递 tools 汇总后的结构化摘要。
   - 后续新增 LLM workflow 时必须继续禁止 raw_text、file_path、raw_extracted_text、token/password/key 进入 prompt。

## Phase 10.C 记录

1. `daily_health_brief` LLM 输出安全已做第一轮收口。
   - LLM prompt 已明确禁止诊断、确诊、处方、剂量、停药、正常/异常、高风险/低风险判断，以及自动急救、报警或联系医院/家人承诺。
   - LLM 输出如触发上述危险内容，会 fallback 到规则简报。
   - unsafe LLM 原文不会返回给用户，也不会写入 trace/debug。

2. LLM fallback reason 已收口为安全摘要。
   - 当前允许记录 `llm_disabled`、`daily_brief_use_llm_disabled`、`llm_configuration_error`、`llm_provider_error`、`llm_timeout`、`empty_llm_output`、`llm_response_invalid`、`llm_output_safety_blocked` 等短 reason。
   - 不记录 API key、raw prompt、raw response、raw_text、symptom_text、raw_extracted_text、file_path、token/password、traceback、SQL 或本机路径。

3. 真实 provider 在线 smoke 尚未执行。
   - Phase 10.C 不做真实在线 LLM smoke，不要求真实 API key。
   - `openai_compatible` provider 仍需要后续在受控环境中使用真实配置单独验证。

4. 其他 workflow 尚未接入 LLM。
   - 当前只有 `daily_health_brief` 可选使用 LLM。
   - 后续如接入草稿、提醒、问答或 LangGraph workflow，必须重新 review prompt、权限、Tool Executor、Safety Policy、trace/debug 与 fallback。
