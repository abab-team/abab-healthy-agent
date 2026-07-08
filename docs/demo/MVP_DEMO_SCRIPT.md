# MVP Demo 脚本

建议控制在 5 到 7 分钟内。演示定位是“家庭健康资料整理与受控 Agent 辅助”，不是医疗诊断系统。

## 0. 开场定位

一句话：

> Family Health Agent 是一个面向家庭日常健康管理的移动端 Agent App，支持家庭成员健康资料记录、文档上传与 OCR 草稿整理、健康简报、权限共享、内部 RAG 检索增强，以及可追踪的 Agent 执行链路。

安全边界：

- 不做医学诊断。
- 不给处方、剂量或停药建议。
- 不替代医生判断。
- 写入类动作必须 preview / confirm。

## 1. 登录

展示：

- api-auth mode 登录。
- 设置页可查看当前用户、安全摘要和 data mode。

讲解：

- 当前已支持最小 Auth/JWT。
- demo header 仅用于开发，生产前必须关闭。

## 2. 首页

展示：

- 家庭今日概览。
- 今日待办。
- AI 今日简报入口。
- 快速记录。

讲解：

- 首页不下医学结论，只展示系统内记录与待办。

## 3. 家庭与权限

展示：

- 家庭页成员列表。
- 成员详情。
- 共享权限概览。

讲解：

- 家人数据访问必须经过 family_id 与权限检查。
- Agent 也不能绕过权限。

## 4. AI 管家与 daily health brief

展示：

- AI 管家页。
- 生成今日健康简报。
- Agent Run 详情中的 trace / tool calls / safety checks。

讲解：

- daily_health_brief 默认是规则简报。
- LLM 可选接入，默认关闭；失败 fallback。
- RAG 开启时仅追加系统内安全 citation。

## 5. 受控写入草稿

展示：

- symptom_draft_create preview。
- confirm 后创建待确认草稿。
- medical_event_draft_create preview / confirm。
- alert_create preview / confirm。

讲解：

- preview 不写入。
- confirm 也只创建待确认草稿或普通提醒。
- 不开放通用 tool execution，不允许前端传 `tool_name` / `input_data`。

## 6. 文档上传与 OCR preview

展示：

- 文档上传入口或文档列表。
- document processing job。
- mock OCR preview。
- 从 OCR preview 生成健康事件草稿。

讲解：

- 当前是 mock OCR，不是真实 OCR provider。
- OCR 结果是预览，不是正式健康事实。
- API 不返回本机路径或 `file_path`。

## 7. RAG / citations

展示：

- 通过 API smoke 或 Agent brief 展示系统内 citation。

讲解：

- RAG 当前是 simple/internal retrieval。
- 不接外部医学知识库。
- 不使用 vector DB。
- 不做通用医疗问答。

## 8. 收尾

强调：

- 这是可演示 MVP，不是生产发布包。
- 后续重点：真机 QA、生产部署、安全加固、真实 OCR、RAG 持久化索引、LangGraph。

