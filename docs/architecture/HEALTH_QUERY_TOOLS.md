# Health Query Tools

本文档记录 Phase 16 新增的自然语言健康查询工具边界。

## 定位

这些工具只服务 `chat` workflow 的系统内健康记录查询，不是通用医疗问答，也不是 AI 医生。

工具只能返回系统内已有记录的安全摘要：

- 指标记录摘要
- 血压摘要
- 症状摘要
- 健康事件摘要
- 文档元数据摘要
- 提醒摘要

工具不得输出诊断、处方、剂量、停药建议，也不得把“系统内暂无记录”表达成现实中没有问题。

## 新增工具

| Tool | 权限 | 说明 |
| --- | --- | --- |
| `health_data.metric.summary` | `metrics:view` | 查询单类指标的聚合摘要。 |
| `health_data.metrics.recent` | `metrics:view` | 查询近期指标安全摘要。 |
| `health_record.symptoms.query` | `symptoms:view` | 查询症状记录摘要，不返回 `raw_text`。 |
| `medical_timeline.events.query` | `medical_events:view` | 查询健康事件摘要。 |
| `documents.query` | `documents:view` | 查询文档元数据摘要，不返回 `file_path` / OCR 全文。 |
| `alerts.query` | `alerts:view` | 查询提醒摘要。 |

## 调用边界

- 所有工具必须通过 `AgentToolExecutor` 调用。
- 工具只调用对应模块 service，不直接访问 repository / DB。
- family 查询必须由 Tool Executor 完成 family permission 检查。
- 权限失败时工具不执行，并记录 blocked `agent_tool_calls`。
- 输出只包含安全摘要，不包含 `raw_text`、`symptom_text`、`raw_extracted_text`、`file_path`、token、password、API key。

## 非目标

- 不开放通用 tool execution。
- 不允许前端或用户传入任意 `tool_name` / `input_data`。
- 不调用 LLM。
- 不写入健康业务数据。
- 不新增 migration / model。
