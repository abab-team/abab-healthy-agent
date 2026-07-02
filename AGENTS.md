# AGENTS.md

本文件是 family-health-agent 项目的 Codex / Agent 开发约束。后续任何开发任务都必须先阅读并遵守本文件，以及项目既有架构与实施计划文档。

## 必读文档

每次开始开发前，必须先阅读并以以下文档为准：

1. `CODEX_IMPLEMENTATION_PLAN.md`
2. `家庭健康Agent_项目架构设计_v1.0.md`
3. `docs/architecture/CODEX_IMPLEMENTATION_PLAN_v1.0.md`
4. `docs/architecture/家庭健康Agent_项目架构设计_v1.0.md`

如文档之间存在冲突，优先遵守更严格、更安全、更符合模块边界的要求；仍不明确时，先停止并向项目负责人确认。

## 总原则

- 严格遵守 `CODEX_IMPLEMENTATION_PLAN.md`，按 Phase 顺序推进。
- 当前任务只允许实现被明确要求的任务，不允许顺手实现后续 Phase。
- 不允许重构顶层目录结构。
- 不允许为了赶进度破坏模块边界。
- 不允许把临时代码、演示代码伪装成正式实现。
- 不允许引入与当前任务无关的大规模依赖、框架或目录调整。

## 目录边界

- 顶层目录必须保持项目设计文档中定义的 monorepo 结构。
- 业务模块必须放在 `backend/app/modules/<domain>/`。
- Agent 相关代码必须放在 `backend/app/agent/`。
- 外部系统集成必须放在 `backend/app/integrations/`。
- 后台任务与 worker 必须放在 `backend/app/jobs/` 或 `backend/app/workers/`。
- 文档、Prompt、数据集、工具脚本必须分别放在 `docs/`、`prompts/`、`datasets/`、`tools/`。

## 分层约束

- API 层只负责接收请求、校验参数、调用 service 或 agent_service。
- 不允许把业务逻辑写进 API 层。
- Repository 只负责数据库读写，不写业务决策。
- Service 负责业务逻辑，不依赖 LangGraph。
- Agent Tools 只能调用 service，不允许直接访问数据库。
- LangGraph Workflow 只负责编排流程，不允许直接创建数据库 session。
- Harness 负责 runtime、权限、工具门禁、安全、追踪和错误处理。

## Agent 与 LLM 安全约束

- 不允许 Agent 直接访问数据库。
- 不允许 Tool 自己决定查询谁。
- 不允许 LLM 决定 `current_user_id`、`family_id`、`target_user_id`。
- 不允许 LLM 调用写入工具。
- 不允许绕过权限系统访问家人数据。
- 所有家人数据访问必须经过 `family_id` 与权限检查。
- 所有关键 Agent 执行必须记录 Trace。
- 所有健康输出必须经过 Safety 检查。
- 文档类工具不允许向 LLM 返回真实文件路径。

## 写入与确认约束

- 不允许让未确认的 AI 草稿入库。
- 写入健康档案前必须有明确的用户确认。
- AI 只能生成结构化草稿或自然语言表达，不能直接制造正式健康事实。
- 正式写入必须通过受控 service 与 Harness / Tool Registry 门禁。

## 医疗安全边界

本项目是生活健康管理与风险提醒系统，不是医疗诊断系统。

严禁实现或输出：

- 医学诊断。
- 处方建议。
- 药物剂量建议。
- 开药、停药、换药建议。
- “保证没事”类确定性结论。
- 把“系统无记录”表达成“现实没有问题”。

允许输出：

- 健康数据整理。
- 趋势与异常提醒。
- 就医沟通摘要。
- 建议咨询医生或及时就医的安全提示。
- 已由用户确认或医疗资料明确提供的事实复述。

## 测试与验收

每次任务完成后必须运行与本次变更匹配的检查。可用检查包括但不限于：

- 文档变更：检查 Markdown 文件存在、内容可读、路径正确。
- Python 后端变更：运行格式检查、类型检查或 `pytest`。
- 数据库变更：运行 migration 相关检查。
- 前端变更：运行 lint、typecheck、test 或 build。

如果测试或检查失败，必须先修复失败项，再结束任务。除非失败由外部环境明确阻塞，不能带着可修复失败结束。

## 每次任务完成后的固定输出

每次任务完成后，必须输出：

1. 修改文件。
2. 运行的检查或测试命令。
3. 检查或测试结果。
4. 剩余事项。
5. 如有风险或阻塞，必须明确说明。

## Git 约束

- 提交前必须查看 `git status`。
- 不允许回滚用户已有改动，除非用户明确要求。
- commit message 必须符合当前任务要求或项目 Git 规范。
- 不允许把密钥、Token、真实隐私数据写入仓库。

