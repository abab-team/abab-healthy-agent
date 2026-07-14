# 对话 Runtime 替换 Phase A 架构审计

> 审计日期：2026-07-14
>
> 范围：`chat_workflow`、会话存储、长期记忆、ConversationTask、LangGraph 适配层、聊天 API 与现有 Agent 单元测试。
> 本文只记录现状与迁移边界；不改变生产运行逻辑。

## 结论摘要

当前实现已经具备受控健康查询、家庭权限、ToolExecutor、草稿任务和安全追踪，但它不是以标准角色消息为主的对话 Runtime。

当前连续对话主要依赖 `AgentMessage` 中的安全摘要，以及由这些摘要派生的 `last_intent`、`last_tool_name`、`last_metric_type`、`semantic_topic` 等字段。LLM 每轮收到的是一条拼接后的用户上下文，并非可恢复的 `HumanMessage` / `AIMessage` / `ToolMessage` 序列。现有 LangGraph 图也使用无 checkpointer 的 `StateGraph.compile()`，每次请求从新的临时 state 开始。

因此，附件提出的替换方向合理：新 Runtime 应以 `MessagesState + add_messages + thread_id + Checkpointer` 为会话主链路；既有安全、权限、ToolExecutor 和确认写入边界必须作为受控能力接入，而不是被新 Runtime 替代。

## 1. 当前调用链

```text
POST /api/v1/agent/runs (workflow_type=chat_workflow)
  -> modules/agent/api.py _prepare_session_id()
  -> AgentRuntime.run()
  -> ChatWorkflow.run()
  -> LangGraphExecutionAdapter (可选；当前为手动节点顺序适配)
  -> run_chat_health_query()
  -> memory_service.load_session_context()
  -> route_conversation() / parse_health_query() / apply_session_context()
  -> ConversationManager (草稿任务延续、暂停或取消)
  -> Family Member Resolver
  -> ToolExecutor（仅由受控白名单工具调用）
  -> Health Insight / ConversationResponder / Critic / Output Safety
  -> AgentMessage 安全摘要、AgentToolCall、AgentSafetyCheck、AgentTrace
```

### 1.1 当前每轮发送给 LLM 的 messages

`ConversationResponder._messages()` 构造两个 `LLMMessage`：

1. 一条 `system`：按意图选择健康管家、健康知识或普通对话提示；
2. 一条 `user`：拼接以下文本块：
   - 最多 6 条 `session_summary`；
   - 最多 6 条低敏 `assistant_context`；
   - 最多 1,800 字符的已鉴权 `safe_facts`；
   - 最多 500 字符的本轮用户输入。

这不是完整角色历史。`session_summary` 本身来自 `agent_messages.content_summary`，且只作为摘要文本注入。

## 2. 会话、消息与工具结果

| 审计问题 | 当前事实 | 迁移结论 |
| --- | --- | --- |
| 历史 user / assistant 是否按角色保存 | 是。`agent_messages.role` 保存 `user` 或 `assistant`。 | 可复用为历史显示和迁移期读取，但当前只保存截断安全摘要。 |
| ToolCall 是否持久化 | 是。`agent_tool_calls` 以 `request_id` 关联 trace。 | 保留；V2 要建立 ToolMessage 与该记录的安全关联。 |
| ToolResult 是否持久化 | 仅以 `agent_tool_calls.output_summary` 的安全摘要形式持久化。 | 不可把自然语言摘要反向当作事实；V2 应在 checkpoint 前写入经过裁剪的结构化 ToolMessage。 |
| 下一轮能否恢复上轮结构化 ToolResult | 否。下一轮只恢复部分 `last_*` 元数据和摘要。 | V2 的核心缺口。 |
| session_id 的创建、传递与读取 | API 对 `chat_workflow` 调用 `memory_service.get_or_create_session()`；已有 session 必须属于当前用户；id 透传 Runtime、Trace 与 workflow。 | 可作为 V2 `thread_id` 的稳定映射。 |
| ConversationTask 与消息历史 | `agent_conversation_tasks` 以 `session_id` 关联，只保存短期草稿状态、缺失字段和过期时间。 | 保持独立；V2 state 可投影 active/paused task，不能把其当作健康事实。 |

## 3. 当前连续对话机制与风险

`memory_service.load_session_context()` 读取最近 8 条 `AgentMessage`，挑选一条含 intent、指标或工具字段的消息，形成：

```text
last_intent
last_member_label / last_member_scope
last_metric_type
last_time_range_label / last_time_range_days
last_tool_name
last_write_action
semantic_topic / semantic_scope
summary_lines
```

随后 `apply_session_context()`、router 与 responder 通过 follow-up marker 和特例规则承接“那上个月呢”“不只是血压”“这个数值健康吗”等输入。

风险：

- 完整会话语义被压缩成少量字段，难以支持自然省略、长对话和工具结果承接；
- 继续扩展会导致更多关键字、`last_xxx` 和特例判断；
- assistant 回复摘要不能作为健康事实来源；
- 当前会话 API 能列出消息，但不能恢复可由模型可靠消费的角色消息序列或 ToolMessage。

## 4. 当前 LangGraph 状态与 Checkpointer

项目有两类聊天编排：

1. `LangGraphExecutionAdapter.run_chat_health_query()`：在开关启用时按固定顺序手动调用现有安全节点，然后仍由旧 workflow 执行工具与回答；
2. `ChatHealthQueryGraph`：继承 `CompiledStateGraphRunner`，使用 `StateGraph(BaseAgentGraphState)` 进行编排。

`CompiledStateGraphRunner._compile()` 调用 `graph.compile()`，没有传入 checkpointer。每次 `run()` 都通过 `initial_graph_state()` 创建临时 state 并 `invoke()`。当前图 state 不含标准 messages reducer，未传入 `thread_id` config，也不支持 checkpoint 恢复或 interrupt/resume。

结论：LangGraph 当前负责安全节点可视化编排和 trace 摘要，尚未是持久会话 Runtime。V2 必须独立增加持久 Checkpointer，而不能假定现有图已提供会话恢复。

## 5. Long-term Memory 与 Session State

`agent_memories` 用于长期、低敏偏好记忆，例如“回答保持简洁”。服务显式过滤诊断、处方、剂量、停药和“正常/异常”等不安全主题。

`agent_sessions` / `agent_messages` 是会话摘要存储；`agent_conversation_tasks` 是短期受控草稿状态。三者现在存在职责区分，但 session context 仍把摘要字段当作主要对话语义来源。

V2 规则：

- 长期 memory：仅用户偏好、完成任务说明与允许保存的低敏信息；
- checkpoint：标准消息、已裁剪的 ToolMessage、当前 working state；
- ConversationTask：仅当前待确认草稿状态；
- 健康事实：只能来自业务库经当前轮权限校验后返回的 ToolExecutor 结果。

## 6. 可复用模块

以下模块应原样保留或以适配器接入：

- `AgentRuntime`：trace、输入/输出安全与统一状态流转；
- `AgentToolRegistry` / `AgentToolExecutor`：enabled、confirmation、permission、tool call trace；
- `chat.member_resolver` / `family_context`：成员解析与家庭范围控制；
- 业务 Service 与只读、草稿类工具：仍由 ToolExecutor 调用；
- `AgentSafetyPolicy` 与 `AnswerCriticService`：输出安全和事实忠实性检查；
- `ConversationManager` / `conversation.tasks`：短期草稿暂停、恢复、取消；
- `agent_tool_calls`、`agent_safety_checks`、`agent_traces`：审计与调试记录；
- `AgentSession`：V2 `thread_id` 的稳定宿主。

## 7. 需要降级或替换的旧对话主链路

在 Phase G 验收完成前，以下仅作为兼容/观测/回滚逻辑，不再新增依赖：

- `memory_service.apply_session_context()` 对 `last_*` 和 follow-up marker 的主路由作用；
- `SessionMemoryContext.summary_lines` 作为 LLM 主上下文；
- `ConversationResponder._messages()` 的单条拼接式历史注入；
- `chat_workflow.py` 内 `is_casual_chat_message()`、`build_casual_chat_response()` 和增长式自然语言特例；
- `LangGraphExecutionAdapter` 手动顺序调用节点作为正式聊天会话编排。

可保留到迁移期结束的仅限：旧 session 读取适配器、历史摘要显示、明确标注 legacy 的紧急回滚开关。它们不能接受新的正式会话流量。

## 8. 数据迁移策略

不反推旧摘要为结构化 ToolMessage，也不伪造旧健康事实。

推荐策略：现有 `session_id` 首次收到 V2 消息时开始一个 V2 checkpoint thread；旧 `AgentMessage` 仅可作为标记为 `legacy_summary` 的系统上下文说明，且不参与权限、工具计划或健康结论。旧草稿任务继续由 `AgentConversationTask` 读取。

是否需要新增数据库表/迁移由 Phase B 的 checkpointer 选型决定：

- 若使用 SQL 持久 Checkpointer，需要独立 migration，并评估数据保留、加密和清理策略；
- 不允许在生产会话采用仅进程内 MemorySaver；
- 不允许把完整敏感原文、文件路径、OCR 原文、密钥或 traceback 写入 checkpoint。

## 9. 回滚方案

Phase F 前通过 `CONVERSATION_RUNTIME_V2_ENABLED=false` 保持旧 Runtime 可用；Shadow mode 只能做只读对比，禁止触发写入或重复 ToolExecutor 写入。

回滚条件：V2 连续消息恢复、工具 ToolMessage 关联、权限隔离、输出安全、任务中断/恢复任一项失败。回滚仅切回旧正式链路，保留 V2 checkpoint 作为审计数据，且不得将 V2 结果回写为业务事实。

Phase G 切换前必须具备：纯聊天、工具连续调用、家庭权限、任务恢复、安全 red-team、长会话裁剪、真实 API smoke 与 shadow 对比证据。切换后旧链路必须停止接收新正式流量并有明确删除条件。

## 10. Phase B 前的最小实现建议

1. 新增 `backend/app/agent/conversation_v2/`，与旧实现隔离；
2. 使用 LangGraph `MessagesState` / `add_messages` 定义 `ConversationState`；
3. 先接稳定 `thread_id=session_id` 与持久 Checkpointer；
4. 只实现 `HumanMessage -> assistant` 的标准连续对话，不接健康 Tool；
5. 为每条持久化消息建立安全裁剪；
6. 添加 checkpoint 保存/恢复、角色消息顺序、用户/会话隔离、长对话裁剪测试；
7. Phase C 通过后再引入受控 ToolExecutor adapter。

## 11. Phase A 验收

- [x] 未修改生产逻辑、模型、迁移或 API；
- [x] 已定位当前 messages 构造、session、ToolCall/ToolResult、ConversationTask 与 memory 的关系；
- [x] 已确认现有 LangGraph 没有持久 checkpointer；
- [x] 已列出可复用模块、退役范围、迁移和回滚约束；
- [ ] 等待项目负责人确认后进入 Phase B。
