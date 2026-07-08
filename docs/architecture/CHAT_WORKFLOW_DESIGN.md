# Chat Workflow Design

Phase 16 新增 `chat` 作为面向移动端的自然语言健康查询入口。

## 目标

`chat` workflow 让用户可以用自然语言查询系统内健康记录，例如：

- 最近一周我的血压记录怎么样？
- 我最近 30 天平均睡眠怎么样？
- 系统内有哪些文档资料？
- 今天有哪些待办提醒？

它只整理系统内记录，不生成诊断或治疗建议。

## 流程

1. API 只允许 `workflow_type=chat`，不允许 `chat_workflow`、`tool_name` 或 `input_data`。
2. `AgentRuntime` 先执行 input safety。
3. `chat` workflow 使用 deterministic parser 解析：
   - intent
   - member label
   - time range
   - metric/source type
4. workflow 根据 intent 选择固定只读工具。
5. 工具必须通过 `AgentToolExecutor`，由 Executor 完成 enabled / metadata / permission 检查。
6. workflow 将工具安全摘要组装为用户可读回答。
7. `AgentRuntime` 执行 output safety。
8. trace / safety_checks / agent_tool_calls 可查询。

## 身份与权限

自然语言中的“我、爸爸、妈妈”等只作为展示和解析提示，不决定 `actor_user_id`、`target_user_id` 或 `family_id`。

这些 ID 仍必须来自 API 请求上下文或用户选择，不能由 LLM 或自然语言解析器决定。

## 输出规则

允许：

- 根据系统内记录整理。
- 系统内暂无相关记录。
- 部分信息因权限设置暂不可用。
- 如有明显不适或紧急情况，请联系医生或当地急救服务。

禁止：

- 诊断、确诊。
- 处方、剂量、停药建议。
- 正常 / 异常 / 高风险 / 低风险判断。
- 把系统无记录表达成现实中没有问题。

## 当前限制

- 不调用 LLM。
- 不使用 LangGraph。
- 不写入健康业务数据。
- family 成员自然语言指代仍需要前端后续提供明确选择或上下文。
