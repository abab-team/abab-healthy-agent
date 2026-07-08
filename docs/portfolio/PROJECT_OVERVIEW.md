# Family Health Agent 项目概览

Family Health Agent 是一个面向家庭日常健康资料管理的移动端 Agent MVP。它围绕家庭成员、共享权限、健康记录、文档处理、Agent 工作流和可追踪安全执行链路构建。

## 一句话介绍

一个面向家庭日常健康管理的移动端 Agent App，支持家庭成员健康资料记录、文档上传与 OCR 草稿整理、健康简报、权限共享、内部 RAG 检索增强与安全可追踪 Agent 执行链路。

## 为什么做

家庭健康信息通常分散在聊天、纸质报告、体检资料、随手记录和个人记忆里。项目尝试把这些资料整理成“系统内记录”，再通过受控 Agent 帮助用户生成简报、草稿和提醒。

## 不是什么

- 不是 AI 医生。
- 不是医疗诊断系统。
- 不是自动处方系统。
- 不替代医生判断或治疗建议。

## 当前能力

- FastAPI 后端。
- Expo React Native 移动端。
- Auth/JWT 最小闭环。
- 家庭成员与共享权限。
- 健康档案、指标、症状、医疗事件、文档、报告、提醒等模块基础。
- Agent Runtime / Tool Executor / Safety / Trace。
- 受控 Agent workflows。
- LLM Client 可选接入 daily_health_brief，默认关闭。
- 文档上传、mock OCR、document processing job。
- 内部 RAG simple retrieval 与 citations。
- smoke、测试、部署、QA 和作品集文档。

## 当前状态

Phase 15 收口后，项目达到可演示 MVP 标准：本地/局域网部署可复现，移动端可演示，核心链路可通过 smoke 验证，边界和后续风险有文档记录。

