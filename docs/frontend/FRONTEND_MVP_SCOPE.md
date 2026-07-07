# Frontend MVP Scope

本文档定义 Phase 09 可用前端 / 调试页面的范围。Phase 09 不写 LLM、不做 LangGraph、不做 OCR/upload/RAG、不做移动端最终版，也不追求完整商业 UI；目标是把已有后端 API 与 Agent API 变成可操作、可验收的产品闭环。

## Phase 09 目标

Phase 09 的目标是：

- 做一个可用前端 / 调试页面。
- 验证现有普通业务 API 与 Agent API。
- 让 demo 用户、家庭成员、权限、健康档案、血压、症状、医疗时间线、提醒、Agent run 可视化。
- 支持查看 `generated_content`、trace、tool_calls、safety_checks。
- 不接 LLM。
- 不做 LangGraph。
- 不做真实 OCR/upload/RAG。
- 不做移动端最终版。
- 不做复杂权限后台。
- 不把 demo header 伪装成正式 Auth/JWT。

## Phase 09.2 移动端静态交互与 API 契约准备

Phase 09.2 在 `apps/mobile` 内推进移动端静态交互，不接真实后端 API。

本阶段完成目标：

- 使用本地 mock API 模拟 loading / success / error / empty state。
- 为草稿和提醒 workflow 展示 `confirmation=false` 预览与 `confirmation=true` 确认边界。
- 准备 TypeScript API 契约类型，供 Phase 09.3 接入 FastAPI 时对照。
- 明确移动端不得开放 `tool_name` / `input_data` 通用工具执行入口。

Phase 09.2 不做：

- 真实后端请求。
- 真实 Auth/JWT。
- LLM / LangGraph。
- OCR/upload/RAG。
- 推送通知。

## 最小页面范围

Phase 09 建议包含以下页面：

| 页面 | 目标 | 依赖能力 | MVP 要求 |
| --- | --- | --- | --- |
| Demo 用户切换页 | 选择当前 `X-Current-User-Id` | identity demo users | 清楚标注“开发调试模式” |
| 家庭/成员页 | 查看家庭与成员，选择 target_user_id/family_id | family API | 不允许前端自行猜 target_user_id |
| 权限查看页 | 查看/更新成员共享权限 | permissions API | 显示 `can_create_alerts` |
| 健康档案页 | 查看/编辑健康档案 | health_profile API | 字段清晰、无医疗结论 |
| 血压记录页 | 查看与记录血压 | health_data API | 不显示“正常/异常/高血压/低血压”等诊断判断 |
| 症状记录/草稿页 | 查看症状、创建/确认草稿 | health_record API, Agent API | 明确区分“草稿”和“正式记录” |
| 医疗时间线页 | 查看医疗事件与随访 | medical_timeline API | 诊断字段只做事实展示，不生成建议 |
| 医疗文档占位页 | 展示文档元数据与处理状态 | document_center API | Phase 09 不做真实上传 |
| 提醒页 | 查看/创建普通提醒 | alerts API, Agent API | 强调提醒不是急救报警 |
| Agent 控制台页 | 调用受控 Agent workflow | Agent API | 只显示白名单 workflow |
| Agent Run 详情页 | 查看 run、tool_calls、safety_checks | Agent API | 用于调试可追踪链路 |

## Agent 控制台支持范围

Agent 控制台只支持当前受控 workflow：

- `daily_health_brief`
- `symptom_draft_create`
- `medical_event_draft_create`
- `alert_create`

Agent 控制台必须支持：

- 选择 actor demo user。
- 选择 target user。
- family 场景显式选择 family。
- 设置 confirmation。
- 输入 user_message。
- 查看 generated_content。
- 查看 trace。
- 查看 tool_calls。
- 查看 safety_checks。

Agent 控制台不得支持：

- 直接输入任意 `tool_name`。
- 直接输入任意 `input_data` 来执行工具。
- 通用 tool execution。
- LLM chat。
- LangGraph workflow。
- 急救报警。
- 自动联系医院、家人或紧急联系人。

## 前端边界

Phase 09 不做：

- 真实登录/JWT。
- LLM 聊天。
- LangGraph。
- OCR/upload。
- RAG。
- 移动端发布。
- 商业级 UI polish。
- 医学诊断展示。
- 处方、剂量、停药建议。
- 通用 Agent tool execution 页面。

Phase 09 可以做：

- demo header 用户切换。
- 明确的家庭成员选择。
- API 调试型页面。
- 受控 workflow 表单。
- 草稿确认 UI。
- 安全提示与可追踪结果展示。

## UI 设计原则

- 体现家庭健康档案感，而不是医院后台。
- 清晰、温和、低压力。
- 不像纯聊天机器人；Agent 是可追踪的辅助控制台。
- 强调“根据系统内记录”。
- 强调“待确认草稿”。
- 强调“提醒不是急救”。
- Agent 输出必须可追踪到 trace、tool_calls、safety_checks。
- 权限不足时只显示安全提示，不显示目标成员数据是否存在。
- 无记录时写“系统内暂无相关记录”，不写“身体没问题”。

## Phase 09 验收建议

Phase 09 完成时至少应验证：

- 可以选择 demo 用户并调用普通 API。
- 可以查看家庭成员与权限。
- 可以查看健康档案、血压、症状、医疗事件、提醒。
- 可以调用 4 个受控 Agent workflow。
- 可以查看 Agent run 详情、tool_calls、safety_checks。
- confirmation=false 不会创建草稿或提醒。
- family 权限不足时前端显示安全提示。
- 页面不展示诊断、处方、剂量、停药建议。

## Phase 09.3.E 补充

Phase 09.3.E 只做移动端写入 workflow UI 收口与 QA 文档补齐：

- 写入类页面统一展示 preview / confirm 状态。
- 成功后显示 trace_id 摘要并可进入 Agent Run 详情。
- Agent Run 详情只展示安全摘要。
- 草稿列表仍为 mock，不接正式确认入库。
- 真机 QA 仍需用户按 `docs/frontend/WRITE_WORKFLOW_QA_CHECKLIST.md` 手动完成。

## Phase 09.4 Final Review 补充

Phase 09.4 已完成移动端 MVP 收口：

- MVP 演示脚本：`docs/frontend/MOBILE_MVP_DEMO_SCRIPT.md`。
- MVP 验收清单：`docs/frontend/MOBILE_MVP_ACCEPTANCE_CHECKLIST.md`。
- Phase 09 Final Review：`docs/frontend/PHASE_09_FINAL_REVIEW.md`。

Phase 09 可以视为移动端 MVP 已完成，但它仍不是生产发布包。真实 Auth/JWT、LLM、LangGraph、OCR/upload/RAG、草稿正式确认入库、生产部署和真机视觉 QA 仍需后续阶段完成。
