# Phase 09 Final Review

## 结论

Phase 09 移动端 MVP 已形成可演示闭环：用户可以在 Expo / Web 中查看家庭概览、家庭成员、成员详情，调用 `daily_health_brief`，通过受控 Agent workflow 创建待确认草稿或普通健康提醒，并查看 Agent Run 的安全摘要。

## 完成范围

- `apps/mobile` Expo + React Native + TypeScript MVP。
- mock / api mode 切换。
- `X-Current-User-Id` demo header 支持。
- `/health` 状态展示。
- 家庭 / 成员只读 demo 数据接入。
- 成员健康摘要只读展示。
- `daily_health_brief` API 接入。
- `symptom_draft_create` preview / confirm 接入。
- `medical_event_draft_create` preview / confirm 接入。
- `alert_create` preview / confirm 接入。
- Agent run / tool_calls / safety_checks 安全摘要查询。
- 写入 workflow UI 状态和 QA 文档。
- MVP demo script 与 acceptance checklist。

## 未接入能力

- 真实 Auth/JWT。
- LLM Client。
- LangGraph。
- OCR / upload / RAG。
- 推送通知。
- 草稿正式确认入库。
- 生产部署与真实设备接入。
- 通用 tool execution API，当前仍明确禁止。

## 验证结果

Phase 09.4 执行的验证包括：

- `npm install`
- `npm run typecheck`
- `npm run lint`
- `npx expo export --platform web`
- `npm run web` HTTP 200 smoke，并确认没有残留前端 dev server。
- `scripts/smoke/mobile_backend_smoke.ps1`
- `scripts/smoke/mobile_write_workflows_smoke.ps1`
- `git diff --check`
- 敏感信息扫描。

## 剩余风险

- 真机 Expo Go 视觉 QA 仍需要用户在真实手机上手动完成。
- PostgreSQL / Docker 完整复验取决于本机 Docker Desktop engine 是否可用。
- 当前使用 demo header，不可用于生产。
- 当前移动端 MVP 不是生产发布包。

## 是否可以进入 Phase 10

可以。建议下一阶段进入 **Phase 10：LLM Client 最小封装**。

Phase 10 必须继续保持 Safety Policy、Tool Executor、权限、confirmation 和 trace 边界。

