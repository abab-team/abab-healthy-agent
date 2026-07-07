# Mobile MVP Acceptance Checklist

本文档用于 Phase 09 移动端 MVP 最终验收。

## 页面完整性

- [ ] 首页可访问，展示家庭概览、待办、AI 简报入口、快捷记录和最近动态。
- [ ] 家庭页可访问，展示家庭卡、成员、关系标签、共享状态和邀请入口。
- [ ] 成员详情页可访问，展示成员信息、系统内健康摘要和 mock/API 标识。
- [ ] AI 管家页可访问，展示 daily brief、三个写入 workflow、草稿和 Agent Run 摘要入口。
- [ ] 创建症状草稿、创建健康事件草稿、创建健康提醒页面可访问。
- [ ] Agent Run 详情页只展示安全摘要。
- [ ] 草稿页明确仍为 mock / 后续接入，不做正式确认入库。
- [ ] 设置页展示开发者调试状态。

## API 接入状态

- [ ] `mock` mode 不请求后端。
- [ ] `api` mode 需要显式配置 `EXPO_PUBLIC_API_BASE_URL`。
- [ ] `api` mode 使用 `X-Current-User-Id` demo header。
- [ ] `/health` 状态可在设置页查看。
- [ ] `daily_health_brief` 可通过 API mode 执行。
- [ ] run / tool_calls / safety_checks 可查询安全摘要。

## 写入 Workflow 状态

- [ ] `symptom_draft_create` preview 使用 `confirmation=false`，不写入。
- [ ] `symptom_draft_create` confirm 使用 `confirmation=true`，只创建待确认症状草稿。
- [ ] `medical_event_draft_create` preview 使用 `confirmation=false`，不写入。
- [ ] `medical_event_draft_create` confirm 使用 `confirmation=true`，只创建待确认健康事件草稿。
- [ ] `alert_create` preview 使用 `confirmation=false`，不写入。
- [ ] `alert_create` confirm 使用 `confirmation=true`，只创建普通健康提醒。
- [ ] 成功状态显示 trace_id 摘要并可进入 Agent Run 详情。
- [ ] error、permission denied、safety blocked、network failed 状态不会伪装成功。

## Mock / API / 待接入标识

- [ ] mock 数据明确标注为 mock 或静态预览。
- [ ] API 数据明确标注为 API 或后端只读接口。
- [ ] 待接入功能明确标注为后续接入。
- [ ] 草稿正式确认入库明确标注为未实现。

## 安全文案

- [ ] 页面不输出诊断、处方、剂量建议或停药建议。
- [ ] 页面不把“系统内暂无记录”表达成现实身体没问题。
- [ ] 页面不声称会自动急救、报警、联系医院或联系家人。
- [ ] 提醒页明确普通健康提醒不是急救。
- [ ] 简报和 Agent 结果强调基于系统内记录，不替代医生。

## 真机 QA

- [ ] Expo Go 真机使用电脑局域网 IP，不使用 `localhost`。
- [ ] 手机和电脑在同一 Wi-Fi。
- [ ] 底部 Tab 不遮挡主要按钮。
- [ ] 中文长文本不会撑爆布局。
- [ ] trace_id 以短 ID 或可跳详情方式展示。
- [ ] loading / success / error / empty 状态清楚。
- [ ] Agent Run 详情不会密集到难以阅读。

## 未完成功能与风险

- [ ] 真实 Auth/JWT 未实现。
- [ ] LLM、LangGraph、OCR/upload/RAG 未实现。
- [ ] 草稿正式确认入库未实现。
- [ ] PostgreSQL / Docker 完整复验仍待环境可用后执行。
- [ ] 真机视觉 QA 需要用户手动完成。
- [ ] 当前使用 demo header，不可用于生产。

