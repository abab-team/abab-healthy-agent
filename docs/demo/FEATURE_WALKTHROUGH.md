# 功能走查

## 已可演示

1. 移动端 Expo MVP。
2. mock / api / api-auth 数据模式。
3. Auth/JWT 登录、refresh、logout。
4. 家庭成员与共享权限展示。
5. daily_health_brief。
6. Agent Run trace / tool calls / safety checks。
7. symptom_draft_create preview / confirm。
8. medical_event_draft_create preview / confirm。
9. alert_create preview / confirm。
10. 文档上传 metadata 与安全 response。
11. document processing job 查询。
12. mock OCR preview。
13. OCR preview 到 pending health event draft。
14. 内部 RAG safe retrieval 与 citations。

## 仍未完成

1. 真实 OCR provider。
2. OCR worker 队列。
3. RAG 持久化索引、真实 embedding、vector DB。
4. 外部医学知识库。
5. LangGraph。
6. 生产发布包。
7. 真实推送通知。
8. Native 文件选择器完整体验。
9. 草稿正式确认入库移动端闭环。

## 安全边界

系统只整理系统内记录和待确认草稿，不提供医学诊断、处方、剂量或停药建议。

