# Feature Coverage Matrix

本文档用于把 Family Health Agent 的产品功能、普通 API、Agent Tool、Agent Workflow、前端页面与后续 Phase 建立明确映射。

## 使用目的

- 产品功能不等于 Agent workflow。
- 普通 API 不等于 Agent workflow。
- Agent Tool 不等于 Agent Workflow。
- 当前 Phase 08 只开放了 4 个受控 Agent workflow，不代表产品只有 4 个功能。
- 后续功能会按普通 API、Agent Tool、Agent Workflow、前端页面逐步落地。
- 本矩阵用于判断“已有能力”“仍需补齐能力”“下一阶段优先级”，避免重复实现或把未完成能力写成已完成。

## 状态值规范

当前实现状态统一使用：

- 已完成
- 部分完成
- 未开始
- 后续增强
- 暂不做
- 风险待收口

已实现层级可多选：

- DB
- Migration
- Seed
- Repository
- Service
- API
- Agent Tool
- Agent Workflow
- Frontend
- LLM
- LangGraph
- Docs

## Phase 建议

Phase 08 后建议执行顺序：

- Phase 09：可用前端 / 调试页面
- Phase 10：LLM Client 最小封装
- Phase 11：LLM 安全增强 Agent 输出
- Phase 12：LangGraph Workflows
- Phase 13：文件上传 / OCR / 文档处理增强
- Phase 14：RAG / 健康知识库
- Phase 15：真实 Auth / 部署 / 产品化收口

如果后续判断真实 Auth/JWT 必须早于 LLM，则应在 Phase 09 前端验证后单独做 schema/API review。当前默认先做可用前端，以便把已完成后端闭环变成可见、可操作、可验收的产品闭环。

## 功能覆盖表

| 功能编号 | 产品功能 | 所属模块 | 用户价值 | 当前实现状态 | 已实现层级 | 已实现内容 | 当前是否有普通 API | 当前是否有 Agent Tool | 当前是否有 Agent Workflow | 是否需要前端页面 | 是否需要 LLM | 是否需要 LangGraph | 是否涉及文件上传/OCR/RAG | 是否涉及写入/确认 | 权限/安全风险 | 建议后续 Phase | MVP 优先级 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A-01 | 用户基础资料 | identity | 识别家庭成员与展示基础档案 | 已完成 | DB, Migration, Seed, Repository, Service, API | 用户创建、个人资料读取/更新、demo header 用户识别 | 是 | 否 | 否 | 是 | 否 | 否 | 否 | 是 | 当前仍是 demo header，不是真实登录 | Phase 09, Phase 15 | P0 | Phase 09 做用户切换页，Phase 15 收口真实 Auth |
| A-02 | 登录/会话/refresh token | identity | 支持正式账号会话 | 部分完成 | DB, Migration | 已有 auth/session/token 表地基 | 否 | 否 | 否 | 是 | 否 | 否 | 否 | 是 | 未实现真实认证，不能生产使用 | Phase 15 | P2 | 当前不阻塞前端 demo |
| A-03 | 真实 Auth/JWT | identity | 生产级鉴权 | 未开始 | Docs | 仅保留模型与风险说明 | 否 | 否 | 否 | 是 | 否 | 否 | 否 | 是 | demo header 不能用于生产 | Phase 15 | P1 | 如外部试用提前，需前置 |
| A-04 | Demo Header 当前状态 | identity | 便于开发调试 | 已完成 | API, Docs | `X-Current-User-Id` demo header 可用 | 是 | 否 | 否 | 是 | 否 | 否 | 否 | 否 | 仅限开发调试，不得生产化 | Phase 09, Phase 15 | P0 | 前端 MVP 可用它做用户切换 |
| B-01 | 创建家庭 | family | 建立家庭健康空间 | 已完成 | DB, Migration, Seed, Repository, Service, API | families 与 owner 成员关系 | 是 | 否 | 否 | 是 | 否 | 否 | 否 | 是 | 需要限制当前用户上下文 | Phase 09 | P0 | 前端需可创建/选择家庭 |
| B-02 | 家庭成员 | family | 管理家人关系 | 已完成 | DB, Migration, Seed, Repository, Service, API | family_members、角色、关系标签 | 是 | 否 | 否 | 是 | 否 | 否 | 否 | 是 | 成员查询必须限定 family | Phase 09 | P0 | relationship_label 是家庭内标签 |
| B-03 | 家庭邀请 | family | 邀请成员加入家庭 | 部分完成 | DB, Migration | invitation 表已建 | 部分 | 否 | 否 | 是 | 否 | 否 | 否 | 是 | 邀请码安全与过期策略需继续收口 | Phase 15 | P2 | MVP 可先用 demo 成员 |
| B-04 | 成员权限 | permissions | 控制家人可见/可写范围 | 已完成 | DB, Migration, Seed, Repository, Service, API | view/create/generate/export 权限，含 `can_create_alerts` | 是 | 否 | 否 | 是 | 否 | 否 | 否 | 是 | 权限不足不得泄露数据存在性 | Phase 09 | P0 | 前端需有权限查看/调试页 |
| B-05 | 权限审计 | permissions | 追踪谁改了共享权限 | 已完成 | DB, Migration, Repository, Service, API | permission_audit_logs | 是 | 否 | 否 | 后续增强 | 否 | 否 | 否 | 是 | 审计内容不得包含健康正文 | Phase 09 | P1 | 调试页可只读展示 |
| B-06 | 家庭成员数据查看 | permissions, health_* | 照护者查看授权数据 | 已完成 | API, Service | family member API 统一权限守卫 | 是 | 部分 | 部分 | 是 | 否 | 否 | 否 | 否 | 必须先权限检查再查数据 | Phase 09 | P0 | Agent workflows 也复用权限链路 |
| C-01 | 健康档案 profile | health_profile | 查看基础健康档案 | 已完成 | DB, Migration, Seed, Repository, Service, API, Agent Tool | profile 读写 API、`health_profile.get` | 是 | 是 | 间接用于 daily_health_brief | 是 | 否 | 否 | 否 | 是 | family 访问需 profile:view | Phase 09 | P0 | Agent 输出只做整理 |
| C-02 | 基础健康信息 | health_profile | 保存身高、血型、目标等 | 已完成 | DB, API | health_profiles 字段 | 是 | 是 | 部分 | 是 | 否 | 否 | 否 | 是 | 敏感字段需脱敏 | Phase 09 | P0 | 与 C-01 合并页面 |
| C-03 | 健康指标 | health_data | 跟踪体重、步数等指标 | 部分完成 | DB, Migration, Seed, Repository, Service, API | health_metrics 与基础 API | 是 | 部分 | 否 | 是 | 否 | 否 | 否 | 是 | 当前无 family_id，依赖 user-owned facts + permission access | Phase 09 | P1 | 后续补更多 Agent tools |
| C-04 | 血压记录 | health_data | 记录和查看血压趋势 | 已完成 | DB, Migration, Seed, Repository, Service, API, Agent Tool | blood_pressure_records、summary tool | 是 | 是 | 间接用于 daily_health_brief | 是 | 否 | 否 | 否 | 是 | 不输出正常/异常/高血压等诊断词 | Phase 09 | P0 | 前端 MVP 重点页 |
| C-05 | 健康数据导入任务 | health_data | 批量导入数据 | 部分完成 | DB, Service | import job 地基 | 部分 | 否 | 否 | 后续增强 | 否 | 否 | 否 | 是 | 数据清洗与来源可信度需增强 | Phase 13 | P3 | 非 Phase 09 MVP |
| D-01 | 症状记录 | health_record | 记录健康随手记 | 已完成 | DB, Migration, Seed, Repository, Service, API, Agent Tool | symptom_records API 与 summary tool | 是 | 是 | 间接用于 daily_health_brief | 是 | 否 | 否 | 否 | 是 | 不能推断病因 | Phase 09 | P0 | 前端需快速记录 |
| D-02 | 症状草稿 | health_record | 先生成待确认草稿 | 已完成 | DB, Migration, Repository, Service, API, Agent Tool, Agent Workflow | pending health_record_drafts | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 是 | 未确认草稿不得变正式事实 | Phase 09 | P0 | `symptom_draft_create` |
| D-03 | 草稿确认 | health_record | 用户确认后写正式事实 | 部分完成 | Service, API | 普通 API 支持确认链路 | 是 | 否 | 否 | 是 | 后续增强 | 后续增强 | 否 | 是 | 必须明确用户确认 | Phase 09, Phase 12 | P0 | Agent 不自动 confirm |
| D-04 | Agent 创建症状草稿 | health_record, agent | 通过受控 Agent API 创建草稿 | 已完成 | Agent Tool, Agent Workflow, API | `health_record.symptom_draft.create` + `symptom_draft_create` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 是 | confirmation=false 不写入 | Phase 09 | P0 | 已通过 API 开放 |
| D-05 | 症状时间线/摘要 | health_record, medical_timeline | 整理近期症状 | 部分完成 | API, Agent Tool | summary tool 与 API 摘要 | 是 | 是 | 部分 | 是 | 后续增强 | 后续增强 | 否 | 否 | 不输出病因推断 | Phase 09, Phase 12 | P1 | 可先用确定性摘要 |
| E-01 | 医疗事件 | medical_timeline | 保存体检、就诊、手术等事件 | 已完成 | DB, Migration, Seed, Repository, Service, API | medical_events API | 是 | 部分 | 否 | 是 | 否 | 否 | 否 | 是 | diagnosis_text 只能来自确认资料/用户输入 | Phase 09 | P0 | 前端时间线重点 |
| E-02 | 医疗事件草稿 | document_processing, medical_timeline | 从资料或输入生成待确认事件 | 已完成 | DB, Migration, Repository, Service, API, Agent Tool, Agent Workflow | medical_event_drafts 与 `medical_event_draft_create` | 是 | 是 | 是 | 是 | 后续增强 | 后续增强 | 涉及文档时是 | 是 | source document/extraction 不可跨 user/family | Phase 09 | P0 | 目前不做 OCR |
| E-03 | 就医记录整理 | medical_timeline, export | 给就医前沟通提供资料 | 部分完成 | Service, API, Agent Tool | followups list tool，事件摘要 API | 是 | 是 | 候选 | 是 | 后续增强 | 后续增强 | 可能涉及文档 | 否 | 不给治疗方案 | Phase 12 | P1 | 后续做 visit_preparation_brief |
| E-04 | 复查/随访信息 | medical_timeline | 管理 follow-up | 已完成 | DB, API, Agent Tool | `medical_timeline.followups.list` | 是 | 是 | 间接用于 daily_health_brief | 是 | 否 | 否 | 否 | 是 | 不输出治疗建议 | Phase 09 | P1 | 与提醒页联动 |
| E-05 | Agent 创建医疗事件草稿 | document_processing, agent | 受控生成待确认医疗事件草稿 | 已完成 | Agent Tool, Agent Workflow, API | `document_processing.medical_event_draft.create` | 是 | 是 | 是 | 是 | 否 | 否 | 可能涉及文档元数据 | 是 | 不返回 file_path/raw_extracted_text | Phase 09 | P0 | 已开放受控 workflow |
| F-01 | 医疗文档元信息 | document_center | 管理报告/病历元数据 | 已完成 | DB, Migration, Seed, Repository, Service, API | medical_documents metadata API | 是 | 部分 | 否 | 是 | 否 | 否 | 是 | 是 | response 不返回 file_path | Phase 09 | P1 | Phase 09 做占位页 |
| F-02 | 文档版本 | document_center | 支持资料版本 | 部分完成 | DB, Migration | document_versions 地基 | 部分 | 否 | 否 | 后续增强 | 否 | 否 | 是 | 是 | 文件权限和版本可见性需收口 | Phase 13 | P3 | 非 MVP |
| F-03 | 文档处理任务 | document_processing | 跟踪处理状态 | 已完成 | DB, Migration, Repository, Service, API | processing jobs API | 是 | 否 | 否 | 是 | 后续增强 | 后续增强 | 是 | 是 | 不能跨 family 引用文档 | Phase 13 | P2 | Phase 09 可只读展示 |
| F-04 | 文档抽取结果 | document_processing | 保存结构化抽取结果 | 已完成 | DB, Migration, Repository, Service, API | extraction results API | 是 | 否 | 否 | 是 | 后续增强 | 后续增强 | 是 | 是 | response 不返回 raw_extracted_text 全文 | Phase 13 | P2 | 当前不做真实 OCR |
| F-05 | 文档摘要 | document_processing | 将文档变成可读摘要 | 部分完成 | DB, API | ai_summary 字段与占位链路 | 部分 | 候选 | 候选 | 是 | 是 | 后续增强 | 是 | 是 | 不得生成诊断/处方 | Phase 13 | P2 | LLM 后再增强 |
| F-06 | 文档转医疗事件草稿 | document_processing, agent | 从文档产生待确认事件 | 部分完成 | Agent Tool, Agent Workflow | 已有受控 medical_event_draft_create，但不做 OCR | 是 | 是 | 是 | 是 | 后续增强 | 后续增强 | 是 | 是 | 文档 scope 必须严格校验 | Phase 13 | P1 | 后续 `document_to_event_draft` |
| F-07 | 文件上传/OCR 后续状态 | document_center, integrations | 处理真实文件 | 未开始 | Docs | 仅保留 storage/OCR integration 结构 | 否 | 否 | 否 | 是 | 后续增强 | 后续增强 | 是 | 是 | 文件路径、隐私、OCR 供应商风险 | Phase 13 | P2 | Phase 09 不做上传 |
| G-01 | daily_reports | reports | 保存每日系统报告 | 已完成 | DB, Migration, Seed, Repository, Service, API | daily_reports API | 是 | 部分 | 否 | 是 | 后续增强 | 后续增强 | 否 | 是 | 唯一约束为 user_id + report_date | Phase 09 | P1 | Agent 当前不写 daily_reports |
| G-02 | 每日健康简报 | reports, agent | 根据系统内记录生成简报 | 已完成 | Agent Tool, Agent Workflow, API | `daily_health_brief` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 必须强调系统内记录且不替代医生 | Phase 09 | P0 | 当前 deterministic，无 LLM |
| G-03 | 每周/月度健康总结 | reports | 长周期整理 | 未开始 | Docs | 候选 workflow 已记录 | 否 | 候选 | 候选 | 是 | 后续增强 | 后续增强 | 否 | 否 | 不输出诊断 | Phase 12 | P2 | weekly/monthly brief |
| G-04 | 家庭健康简报 | reports, family | 照护者看授权成员状态 | 未开始 | Docs | 候选 workflow 已记录 | 否 | 候选 | 候选 | 是 | 后续增强 | 后续增强 | 否 | 否 | family 权限必须逐项检查 | Phase 12 | P1 | caregiver 场景 |
| G-05 | 就医前资料整理报告 | reports, export | 辅助问诊沟通 | 部分完成 | Service, API | export/report 地基 | 部分 | 候选 | 候选 | 是 | 是 | 后续增强 | 可能涉及文档 | 否 | 不给治疗方案 | Phase 12, Phase 14 | P1 | 后续 visit_preparation_brief |
| H-01 | alerts | alerts | 管理普通健康提醒 | 已完成 | DB, Migration, Seed, Repository, Service, API, Agent Tool, Agent Workflow | alerts API、`alerts.create`、`alert_create` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 是 | 不是急救报警 | Phase 09 | P0 | `can_create_alerts` 已收口 |
| H-02 | alert_events | alerts | 记录提醒状态变化 | 部分完成 | DB, Service | alert event 地基 | 部分 | 否 | 否 | 后续增强 | 否 | 否 | 否 | 是 | 审计与通知边界需明确 | Phase 15 | P2 | 非 Phase 09 必须 |
| H-03 | 普通健康提醒 | alerts | 记录复查/用药/资料提醒 | 已完成 | API, Agent Workflow | 普通 alert 创建 | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 是 | 不代表医疗建议 | Phase 09 | P0 | 前端需强调“提醒不是急救” |
| H-04 | 复查提醒 | alerts, medical_timeline | 避免漏复查 | 部分完成 | DB, API | follow_up 与 alerts 可关联 | 是 | 候选 | 候选 | 是 | 否 | 后续增强 | 否 | 是 | 不判断病情严重程度 | Phase 09, Phase 12 | P1 | 可先手动创建 |
| H-05 | 记录提醒 | alerts | 提醒补充数据 | 部分完成 | API | 普通提醒可承载 | 是 | 候选 | 候选 | 是 | 否 | 否 | 否 | 是 | 不自动催促医疗行为 | Phase 09 | P1 | |
| H-06 | Agent 创建提醒 | alerts, agent | 通过受控 Agent API 创建提醒 | 已完成 | Agent Tool, Agent Workflow, API | `alert_create` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 是 | 急症/自伤请求 blocked | Phase 09 | P0 | |
| H-07 | 非急救报警边界 | alerts, safety | 防止误导用户 | 已完成 | Safety, Docs, Tests | Safety Policy 阻断危险请求 | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 是 | 不自动报警/联系医院/家人 | Phase 09 | P0 | 文案需持续保守 |
| I-01 | AgentRuntime | agent | 创建可追踪 Agent run | 已完成 | Agent Workflow, Service | trace 生命周期 | 否 | 否 | 是 | 调试页 | 否 | 否 | 否 | 否 | trace 不得停留 running | Phase 09 | P0 | |
| I-02 | Safety Policy | agent | 医疗安全边界 | 已完成 | Agent Workflow, Service | input/output deterministic safety | 否 | 否 | 是 | 调试页 | 否 | 否 | 否 | 否 | 不输出诊断/处方/剂量/停药 | Phase 09 | P0 | |
| I-03 | Tool Registry | agent | 管理工具元数据 | 已完成 | Agent Tool, Docs | metadata、risk、permission、confirmation | 否 | 是 | 否 | 调试页 | 否 | 否 | 否 | 否 | 非 system tool 必须声明权限 | Phase 09 | P0 | |
| I-04 | Tool Executor | agent | 统一执行工具门禁 | 已完成 | Agent Tool, Service | enabled/metadata/confirmation/permission/tool_call | 否 | 是 | 是 | 调试页 | 否 | 否 | 否 | 是 | tool_call 摘要需脱敏 | Phase 09 | P0 | |
| I-05 | Tool Call 记录 | agent | 审计工具调用 | 已完成 | DB, Migration, Service, API | agent_tool_calls 查询 | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 不保存 raw_text/file_path/token | Phase 09 | P0 | |
| I-06 | Safety Check 记录 | agent | 审计安全检查 | 已完成 | DB, Migration, Service, API | safety_checks 查询 | 是 | 否 | 是 | 是 | 否 | 否 | 否 | 否 | 不返回完整长文本 | Phase 09 | P0 | |
| I-07 | Trace 查询 | agent | 调试 Agent run | 已完成 | DB, Migration, Service, API | trace 查询 owner-only | 是 | 否 | 是 | 是 | 否 | 否 | 否 | 否 | 不能查其他 actor 的 trace | Phase 09 | P0 | |
| I-08 | 受控 workflow | agent | 白名单方式开放 Agent 能力 | 已完成 | API, Agent Workflow | 4 个受控 workflow | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 视 workflow | 拒绝未知 workflow | Phase 09 | P0 | |
| I-09 | 通用 tool execution 禁止状态 | agent | 防止任意工具被调用 | 已完成 | API, Docs, Tests | 拒绝 `tool_name` / `input_data` | 是 | 是 | 是 | 调试页 | 否 | 否 | 否 | 是 | 不开放直接 tool API | Phase 09 | P0 | |
| J-01 | daily_health_brief | agent | 生成系统内健康简报 | 已完成 | Agent Workflow, API | 通过 5 个只读 tools | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 不写 daily_reports | Phase 09 | P0 | |
| J-02 | symptom_draft_create | agent | 创建症状待确认草稿 | 已完成 | Agent Workflow, API | 受控 draft workflow | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 是 | confirmation=false 不写入 | Phase 09 | P0 | |
| J-03 | medical_event_draft_create | agent | 创建医疗事件待确认草稿 | 已完成 | Agent Workflow, API | 受控 draft workflow | 是 | 是 | 是 | 是 | 否 | 否 | 可能涉及文档 | 是 | 不写正式 medical_event | Phase 09 | P0 | |
| J-04 | alert_create | agent | 创建普通健康提醒 | 已完成 | Agent Workflow, API | 受控提醒 workflow | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 是 | 非急救、非自动联系 | Phase 09 | P0 | |
| K-01 | weekly_health_brief | agent | 周度简报 | 未开始 | Docs | 候选 workflow | 否 | 候选 | 否 | 是 | 后续增强 | 后续增强 | 否 | 否 | 不诊断 | Phase 12 | P2 | |
| K-02 | monthly_health_brief | agent | 月度简报 | 未开始 | Docs | 候选 workflow | 否 | 候选 | 否 | 是 | 后续增强 | 后续增强 | 否 | 否 | 不诊断 | Phase 12 | P3 | |
| K-03 | family_health_brief | agent, family | 家庭授权视图 | 未开始 | Docs | 候选 workflow | 否 | 候选 | 否 | 是 | 后续增强 | 后续增强 | 否 | 否 | 逐成员权限 | Phase 12 | P1 | |
| K-04 | blood_pressure_trend_brief | agent, health_data | 血压趋势整理 | 未开始 | Docs | 候选 workflow | 否 | 候选 | 否 | 是 | 后续增强 | 后续增强 | 否 | 否 | 不说高血压/低血压诊断 | Phase 12 | P1 | |
| K-05 | symptom_timeline_brief | agent, health_record | 症状时间线整理 | 未开始 | Docs | 候选 workflow | 否 | 候选 | 否 | 是 | 后续增强 | 后续增强 | 否 | 否 | 不推断病因 | Phase 12 | P1 | |
| K-06 | visit_preparation_brief | agent, export | 就医前资料整理 | 未开始 | Docs | 候选 workflow | 否 | 候选 | 否 | 是 | 是 | 后续增强 | 可能涉及文档 | 否 | 不给治疗方案 | Phase 12 | P1 | |
| K-07 | followup_plan_summary | agent, medical_timeline | 复查计划整理 | 未开始 | Docs | 候选 workflow | 否 | 候选 | 否 | 是 | 后续增强 | 后续增强 | 否 | 否 | 不判断严重程度 | Phase 12 | P2 | |
| K-08 | document_summary | agent, document_processing | 文档摘要 | 未开始 | Docs | 候选 workflow | 否 | 候选 | 否 | 是 | 是 | 后续增强 | 是 | 否 | 不返回 file_path | Phase 13 | P2 | |
| K-09 | document_to_event_draft | agent, document_processing | 文档转事件草稿 | 部分完成 | Agent Tool, Agent Workflow | 目前无 OCR，只支持受控草稿入口 | 是 | 是 | 是 | 是 | 是 | 后续增强 | 是 | 是 | 需确认后才正式写入 | Phase 13 | P1 | |
| K-10 | caregiver_brief | agent, family | 照护者摘要 | 未开始 | Docs | 候选 workflow | 否 | 候选 | 否 | 是 | 后续增强 | 后续增强 | 否 | 否 | 不泄露未授权成员数据 | Phase 12 | P1 | |
| K-11 | daily_report_generate | agent, reports | 生成并保存日报 | 未开始 | Docs | 候选 workflow | 否 | 候选 | 否 | 是 | 是 | 后续增强 | 否 | 是 | 写入前需确认/规则边界 | Phase 12 | P2 | 当前 daily_health_brief 不入库 |
| L-01 | 最小可用移动端 | apps/mobile | 让已有能力可操作 | 已完成 | Frontend, Docs | Expo + React Native MVP，支持 mock/api mode | 是 | 否 | 是 | 是 | 否 | 否 | 否 | 视页面 | demo header 风险 | Phase 09 | P0 | Phase 09.4 收口 |
| L-02 | Demo 用户调试 | apps/mobile, identity | 选择 demo 用户验收流程 | 部分完成 | Frontend, Docs | 设置页展示 `X-Current-User-Id`，环境变量配置 | 是 | 否 | 否 | 是 | 否 | 否 | 否 | 否 | 不得伪装真实 Auth | Phase 09, Phase 15 | P0 | 后续可做用户切换页 |
| L-03 | 家庭成员选择 | apps/mobile, family | 选择目标成员 | 已完成 | Frontend | 家庭页、成员详情、写入 workflow 目标成员选择 | 是 | 否 | 是 | 是 | 否 | 否 | 否 | 否 | 必须传明确 target_user_id/family_id | Phase 09 | P0 | |
| L-04 | 健康档案摘要 | apps/mobile, health_profile | 查看档案摘要 | 部分完成 | Frontend | 成员详情展示系统内只读摘要 | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 字段校验与脱敏 | Phase 09, Phase 12 | P0 | 编辑页后续增强 |
| L-05 | 血压/症状摘要 | apps/mobile, health_data, health_record | 查看摘要与创建草稿 | 已完成 | Frontend | 成员详情摘要、症状草稿 workflow | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 是 | 不渲染诊断判断 | Phase 09 | P0 | |
| L-06 | 健康事件草稿页 | apps/mobile, medical_timeline | 创建待确认健康事件草稿 | 已完成 | Frontend | `create-health-event-draft` preview/confirm | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 是 | 不写正式 medical_event | Phase 09 | P0 | |
| L-07 | 文档页 | apps/mobile, document_center | 展示文档元数据占位 | 未开始 | Docs | Phase 09 不做真实上传/OCR | 否 | 否 | 否 | 后续增强 | 否 | 否 | 是 | 是 | Phase 09 不做真实上传 | Phase 13 | P2 | |
| L-08 | 提醒创建页 | apps/mobile, alerts | 创建普通健康提醒 | 已完成 | Frontend | `create-alert` preview/confirm | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 是 | 强调不是急救 | Phase 09 | P0 | |
| L-09 | Agent 简报页 | apps/mobile, agent | 调用 daily brief | 已完成 | Frontend | 首页/AI 管家调用 `daily_health_brief` | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 否 | 显示 trace 可追踪 | Phase 09 | P0 | |
| L-10 | Agent 草稿创建页 | apps/mobile, agent | 创建待确认草稿 | 已完成 | Frontend | 症状草稿、健康事件草稿 preview/confirm | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 是 | confirmation UI 必须清晰 | Phase 09 | P0 | |
| L-11 | 草稿确认页 | apps/mobile | 用户确认后写正式事实 | 部分完成 | Frontend, Docs | 草稿页仍为 mock，明确不正式入库 | 否 | 否 | 否 | 是 | 否 | 否 | 否 | 是 | 不自动确认 | Phase 12, Phase 15 | P0 | 正式确认入库后续 |
| L-12 | Trace/Tool/Safety 调试页 | apps/mobile, agent | 验证审计链路 | 已完成 | Frontend | Agent Run 详情安全摘要 | 是 | 否 | 否 | 是 | 否 | 否 | 否 | 否 | 只看自己的 run | Phase 09 | P0 | |
| M-01 | LLM Client | agent, integrations | 统一模型调用 | 未开始 | Docs | 原计划保留，顺序后移 | 否 | 否 | 否 | 后续增强 | 是 | 否 | 否 | 否 | API key 与输出安全风险 | Phase 10 | P2 | |
| M-02 | LLM Prompt 管理 | prompts | 可追踪 prompt | 未开始 | Docs | 原计划保留 | 否 | 否 | 否 | 后续增强 | 是 | 否 | 否 | 否 | prompt 不散落代码 | Phase 10 | P2 | |
| M-03 | LLM 输出安全检查 | agent | 防止危险表达 | 部分完成 | Safety, Docs | deterministic safety 已有，LLM 输出增强未做 | 否 | 否 | 否 | 后续增强 | 是 | 否 | 否 | 否 | unsafe output 必须被替换 | Phase 11 | P1 | |
| M-04 | LangGraph Workflows | agent | 复杂编排 | 未开始 | Docs | 原计划后移 | 否 | 否 | 否 | 后续增强 | 是 | 是 | 否 | 视 workflow | 不得绕过 Tool Executor | Phase 12 | P2 | |
| M-05 | OCR/upload | document_center, integrations | 真实资料入口 | 未开始 | Docs | storage/OCR 结构预留 | 否 | 否 | 否 | 是 | 后续增强 | 后续增强 | 是 | 是 | 文件路径与隐私 | Phase 13 | P2 | |
| M-06 | RAG/健康知识库 | knowledge | 常识解释与来源引用 | 未开始 | Docs | knowledge 模块预留 | 部分 | 候选 | 候选 | 是 | 是 | 后续增强 | 否 | 否 | 不得据此诊断 | Phase 14 | P3 | |
| M-07 | 部署 | infra, operations | 可稳定运行 | 部分完成 | Docker, Docs | dev compose 已有 | 否 | 否 | 否 | 后续增强 | 否 | 否 | 否 | 否 | 生产密钥和备份 | Phase 15 | P2 | |
| M-08 | 移动端生产化 | apps/mobile | 后续扩展为可发布应用 | 部分完成 | Frontend, Docs | MVP 已完成，生产化未完成 | 是 | 是 | 是 | 是 | 否 | 否 | 否 | 视功能 | 不绕过后端权限 | Phase 15+ | P2 | 仍需 Auth、发布包、真机 QA |

## 当前结论

Phase 09 已完成移动端 MVP，让已有 API、权限、Agent workflow、trace/tool_calls/safety_checks 可以在 Expo App 中被看见和验证。下一步建议进入 Phase 10：LLM Client 最小封装。LangGraph、OCR/upload、RAG 继续后移。
