# 模块边界规范

本文档定义 family-health-agent 的模块依赖方向与使用边界。模块边界是项目长期可维护性的核心约束，不得为了短期进度绕开。

## 总体依赖方向

允许的高层方向：

```text
API -> Service -> Repository -> Database
API -> AgentService -> Agent Harness / Workflow -> Agent Tools -> Service
Jobs / Workers -> Service
Integrations -> 外部系统
Service -> Integrations
```

不允许的方向：

```text
API -> Repository
API -> Database
Workflow -> Database
Agent Tool -> Repository
Agent Tool -> Database
LLM -> user_id / family_id / target_user_id 决策
LLM -> 写入工具
```

## modules 与 agent

- `backend/app/modules/` 保存业务事实、业务规则、service、repository、schema、API。
- `backend/app/agent/` 保存 Agent runtime、harness、tools、workflow、LLM client、prompt 适配。
- Agent 可以通过 Agent Tools 调用业务 service。
- 业务 modules 不应依赖 LangGraph workflow。
- 业务 modules 不应依赖具体 LLM provider。
- Agent 不允许直接访问数据库，不允许直接 import repository 或 model 完成查询。

## modules 之间的依赖

- `identity` 是用户身份基础模块，可被家庭、权限、审计等模块引用。
- `family` 负责家庭空间与成员关系，是家人数据访问的前置边界。
- `permissions` 负责共享权限判断，不得被前端或 Agent 绕过。
- `health_profile`、`health_data`、`health_record`、`medical_timeline` 等健康模块必须以 `user_id`、必要时以 `family_id` 建立清晰归属。
- `reports` 和 `alerts` 可以读取健康数据、症状、医疗事件等 service 输出，不直接跨模块查库。
- `document_processing` 可以消费 `document_center` 中的原始资料，但正式医疗事件写入必须经过草稿确认。
- `audit` 用于审计访问、隐私事件和 Agent trace，不应承载业务主流程决策。

跨模块调用优先通过 service 接口，不直接 import 其他模块 repository。

## integrations 使用边界

- `backend/app/integrations/` 只封装外部服务或基础设施适配，如 LLM、OCR、存储、消息、健康平台、观测系统。
- integrations 不保存业务事实。
- integrations 不决定权限。
- integrations 不决定当前用户、家庭或目标成员。
- integrations 出错时必须由调用方转换为项目内可处理错误。
- 真实外部服务调用必须可 mock，测试环境不依赖真实 LLM API。

## document 边界

- 原始文件路径只允许内部服务使用。
- Agent 工具不得向 LLM 返回真实 `file_path`。
- 文档读取必须通过 `document_center` 或 `document_processing` service。
- AI 提取结果只能作为草稿，用户确认后才可写入正式医疗事件。

## 权限边界

- 家人数据访问必须经过 `family_id` 和 permission check。
- 权限不足时不得透露数据是否存在。
- `current_user_id`、`family_id`、`target_user_id` 必须来自认证上下文、用户选择或后端解析结果，不得由 LLM 自由决定。

