# 面试讲解提纲

## 项目背景

家庭健康信息常常分散，用户需要一个能长期整理资料、照顾家庭共享权限、并能辅助生成简报和待确认草稿的工具。

## 为什么不是 AI 医生

医疗诊断和处方是高风险场景。这个项目选择做“生活健康资料整理 + 安全 Agent 辅助”：

- 不诊断。
- 不处方。
- 不给剂量。
- 不建议停药。
- 强调系统内记录和医生判断。

## 核心业务流程

1. 用户登录。
2. 选择家庭和成员。
3. 查看健康资料。
4. Agent 生成健康简报。
5. 用户通过 preview / confirm 创建待确认草稿或提醒。
6. 文档上传后通过 mock OCR 生成 preview。
7. OCR preview 可进入待确认健康事件草稿。
8. Agent Run 可查看 trace、tool calls、safety checks。

## 架构亮点

- 模块化单体。
- 统一权限系统。
- Agent Runtime / Tool Executor / Safety / Trace。
- 写入确认边界。
- LLM 可选接入和 fallback。
- 内部 RAG safe citations。
- 完整 smoke 与 QA 文档。

## 关键安全设计

- LLM 不决定 user/family/target。
- Agent 不直接访问数据库。
- Tool 只调用 service。
- 家人数据必须经过 family permission。
- 写入类 workflow 必须确认。
- OCR/RAG/LLM 不直接制造正式健康事实。

## 当前不足

- 未正式生产部署。
- 真实 OCR provider 未接入。
- RAG 未持久化，未接 vector DB。
- LangGraph 未实现。
- 真机 QA 仍需持续补齐。
- 草稿正式确认入库移动端闭环仍待实现。

## 后续计划

优先顺序：

1. 完成用户真机 QA 与录屏。
2. 生产配置安全复核。
3. 真实 OCR provider 受控接入。
4. RAG 持久化索引和权限同步 review。
5. PostgreSQL/云部署。
6. LangGraph workflow 重构。

