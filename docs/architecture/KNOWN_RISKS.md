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

## Phase 16 记录

1. 自然语言成员指代仍是提示信息，不是身份授权来源。
   - `chat` workflow 可以解析“我、爸爸、妈妈、家人”等 member label。
   - 解析结果只用于回答文案和意图辅助，不能决定 `actor_user_id`、`target_user_id` 或 `family_id`。
   - API 调用方仍必须显式传入目标用户与 family context；family 数据访问继续由 Tool Executor + permissions 系统判断。
   - 后续如要支持前端从自然语言中选择家庭成员，需要单独做 UX 与权限 review。

2. `chat` workflow 当前为 deterministic parser。
   - Phase 16 不调用 LLM，不接 LangGraph。
   - 未识别意图会返回安全提示，不回退到通用问答。
   - 不开放 `tool_name` / `input_data`，避免变成通用 tool execution。

## Phase 17 记录

1. LangGraph 当前为默认关闭的薄适配层。
   - `LANGGRAPH_ENABLED=false` 时完全保持 Phase 16 行为。
   - 开启 `LANGGRAPH_ENABLED=true` 与 `LANGGRAPH_CHAT_QUERY_ENABLED=true` 后，当前仅为 `chat` workflow 记录安全 graph node summary。
   - 本阶段没有引入复杂多节点状态机，也没有让 graph 直接调用 tool、查数据库或写业务数据。

2. `daily_health_brief` graph 仅保留配置开关。
   - `LANGGRAPH_DAILY_BRIEF_ENABLED=false` 默认关闭。
   - 本阶段不改 `daily_health_brief` 执行路径，避免影响已稳定的 LLM/RAG/fallback 逻辑。
   - 后续如要将 daily brief 真正迁移到 graph，需要单独 review 规则简报、LLM fallback、RAG citations 与 safety output 例外。
   - 后续如接入草稿、提醒、问答或 LangGraph workflow，必须重新 review prompt、权限、Tool Executor、Safety Policy、trace/debug 与 fallback。
## Phase 11 记录

1. 真实 provider smoke 仍不是生产承诺。
   - Phase 11 新增了真实 provider 受控 smoke 路径，但默认仍不联网、不需要 key。
   - 只有显式设置 `LLM_REAL_SMOKE_ENABLED=true` 且提供本地 `LLM_API_KEY` 时才会调用真实 provider。
   - smoke 通过只说明最小连通性可用，不代表成本、稳定性、限流、合规、监控或生产 SLA 已完成。

2. daily_health_brief LLM 质量评估使用合成摘要。
   - 评估 harness 不使用真实用户健康数据。
   - 合成用例可以覆盖基础安全边界，但不能替代真实产品灰度、人工 QA 或长期回归评估。
   - 真实 provider 可能存在模型版本漂移和输出风格波动，必须继续保留规则简报 fallback。

3. LLM 调试信息仍必须保持摘要化。
   - 允许记录 `llm_used`、`llm_provider`、`llm_model`、`fallback_used`、`fallback_reason`、`safety_filtered`。
   - 禁止记录 API key、raw prompt、raw response、raw_text、symptom_text、raw_extracted_text、file_path、token/password/key、traceback、SQL 或本机敏感路径。

## Phase 12.A 记录

1. Auth/JWT 地基已建立，但尚未全局接管 current user。
   - Phase 12.A 新增了 login、refresh、logout、`/auth/me` 和最小 register。
   - 既有业务 API 仍保留 `X-Current-User-Id` demo header，不在本阶段强制改为 Bearer token。
   - 后续 Phase 12.B 必须专门 review current user dependency、demo header 关闭策略和移动端迁移路径。

2. 默认认证配置仍偏开发模式。
   - 默认 `AUTH_ENABLED=false`、`AUTH_DEMO_LOGIN_ENABLED=true`，方便现有 demo 与 smoke 不被破坏。
   - 生产或外部试用前必须设置强 `JWT_SECRET_KEY`，并明确关闭或限制 demo header。
   - `.env.example` 只提供占位值，真实 `.env` 与密钥不得提交。

3. Phase 12.A 未实现完整账号体系。
   - 本阶段不实现 OAuth、短信验证码、邮箱验证、找回密码、设备管理、管理员 RBAC 或审计型登录风控。
   - 当前密码策略和 token 策略仅为最小工程地基，后续产品化前需要安全 review。

4. demo 用户密码仅用于本地开发验证。
   - `seed_demo_data.py` 为 demo 用户写入开发用密码哈希，便于 auth smoke。
   - 该 demo 密码不得作为生产账号密码或真实用户初始密码策略。

## Phase 12 Final Review 记录

1. demo header fallback 仍保留。
   - Phase 12.B 已新增 `AUTH_DEMO_HEADER_ENABLED`，并支持生产环境关闭。
   - 默认值仍为 true，以保护本地 demo 和既有 smoke。
   - 生产或外部试用前必须设置 `AUTH_DEMO_HEADER_ENABLED=false`。

2. 移动端 Native token 安全存储尚未完成。
   - 当前 Web 可使用 `localStorage`，Native 环境会退回内存 session。
   - 生产发布前应接入 Expo SecureStore 或等价安全存储。
   - UI 只显示 token 短摘要，不展示完整 token。

3. 账号安全策略仍是最小版本。
   - 当前未实现 OAuth、短信验证码、邮箱验证、找回密码、设备管理、登录失败限流和管理员 RBAC。
   - 这些能力需要后续产品化安全 review。

4. JWT 不替代权限系统。
   - JWT 只识别当前用户。
   - family permissions、Agent Safety、Tool Executor 和 confirmation 仍必须独立执行。
   - 后续任何 API 或 Agent workflow 变更不得把“JWT 用户本人”错误当成家人数据访问授权。
## Phase 13 Document Processing Risks

- Phase 13 only adds a local storage foundation and deterministic mock OCR. No real OCR provider has been integrated or online-smoked.
- `OCR_ENABLED=false` and `OCR_STORE_RAW_TEXT=false` remain the safe defaults. Enabling raw OCR storage requires a separate privacy and retention review.
- The mobile app has a document-processing status UI, but no native file picker or production upload experience yet.
- OCR extraction results are previews for review. They must not be treated as diagnosis, prescription, dosage guidance, or formal health facts.
- `medical_event_draft_create` can create only pending drafts from OCR previews. Formal `medical_events` confirmation remains outside Phase 13.
- Local document storage stores internal storage keys. Any future object-storage backend needs a separate path, ACL, retention, and signed-url review.
## Phase 14 RAG Risks

- RAG is disabled by default with `RAG_ENABLED=false`.
- Phase 14 uses dynamic internal indexing and simple retrieval only. There is no persisted RAG index, vector DB, or real embedding provider.
- RAG only indexes safe summaries and previews. It must not index `raw_text`, `symptom_text`, full `raw_extracted_text`, file paths, local paths, token/password/API key, traceback, SQL, raw prompt, or raw LLM response.
- RAG retrieval depends on current family permissions at query time. If a future persisted index is introduced, permission revocation and deletion synchronization need a separate schema and privacy review.
- `health_metrics` and `blood_pressure_records` still have no `family_id`; Phase 14 continues the existing user-owned facts plus family permission access strategy.
- RAG is not a medical QA system. It must not generate diagnosis, prescription, dosage, stop-medication advice, normal/abnormal judgment, or high/low risk judgment.
- External medical knowledge bases remain out of scope and require a separate safety, source, citation, and compliance review.

## Phase 15 Deployment / QA / Portfolio Risks

- Phase 15 closes the MVP demo path, not a production launch. The project still needs a separate production deployment review before external users or real health data are introduced.
- `AUTH_DEMO_HEADER_ENABLED` remains useful for local development and smoke tests, but production or external trial deployments must set it to `false` and use Bearer token auth.
- Production deployments must use strong random `JWT_SECRET_KEY` and `SECRET_KEY`. Example values in `.env.example` are placeholders only.
- Local SQLite remains acceptable for demos. Production should use PostgreSQL or an equivalent managed database with backup and migration procedures.
- Local document storage is a demo path. Production storage needs persistence, access control, encryption, retention, and malware-scanning review.
- Real-device Expo Go QA still requires manual user validation. Codex can verify web export and smoke scripts, but cannot replace physical device checks for touch targets, line wrapping, network permissions, and visual layout.
- Docker Compose is documented as a development/demo path. It is not a complete production architecture.
- Real OCR provider, OCR worker, RAG persisted index, real embedding provider, vector DB, external medical knowledge base, and LangGraph remain out of scope for Phase 15.
- Portfolio materials must not overstate the project as an AI doctor, diagnostic system, prescription system, or production medical product.

## Phase 26 Production Readiness Risks

- Phase 26 adds production deployment and security readiness checks, but does not perform a real public launch.
- `tools/check_production_readiness.py` and `scripts/smoke/production_readiness_smoke.ps1` are preflight checks. Passing them does not replace infrastructure review, incident response planning, backup restoration drills, or legal/privacy review.
- Production or external trial deployments must keep `AUTH_DEMO_HEADER_ENABLED=false`, `DEBUG=false`, strong secrets, explicit CORS origins, PostgreSQL, and secure object storage.
- Real OCR provider, persistent RAG index, real embedding provider, vector DB, external medical knowledge base, rate limiting, malware scanning, and full observability still require separate implementation and review.
- The system must continue to avoid diagnosis, prescription, dosage, stop-medication guidance, and normal/abnormal medical judgment in production-like environments.

## RC 02 LangGraph Risks

- LangGraph execution is optional and disabled by default. A production-like
  rollout must enable workflow flags gradually and monitor graph fallback rates.
- Document extraction and daily report graph paths are MVP previews. They do not
  add persistent extraction/report storage beyond already reviewed services.
- Health knowledge QA remains limited to internal safe context. External medical
  knowledge requires a separate source, safety, and citation review.
- Graph node summaries are intentionally safe and compact. They are not a raw
  graph replay log and must not be expanded to include raw prompts, raw LLM
  responses, file paths, raw OCR, SQL, tokens, keys, `tool_name`, or
  `input_data`.
