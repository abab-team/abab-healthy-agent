# API Contract Checklist

本文档用于 Phase 09.3 正式接入 FastAPI 前的契约核对。Phase 09.2 只完成 mock API 与 TypeScript 类型准备。

## 接入前必须确认

- API base URL 是否使用局域网 IP，而不是手机上的 `localhost`。
- 是否仍使用 `X-Current-User-Id` demo header，并明确标注开发调试模式。
- 每个请求是否显式传入 `target_user_id`。
- family 场景是否显式传入 `family_id`。
- 前端是否没有自行猜测 `current_user_id`、`family_id`、`target_user_id`。
- 前端是否没有开放 `tool_name` / `input_data`。

## 页面所需接口

| 页面 | 需要确认的接口 |
| --- | --- |
| 首页 | 当前用户、家庭概览、待办、最近动态、Agent 简报入口 |
| 家庭 | 家庭成员、成员详情、共享权限概览 |
| 草稿 | 草稿列表、草稿状态更新、草稿确认 |
| 创建症状草稿 | `POST /api/v1/agent/runs` with `symptom_draft_create` |
| 创建健康事件草稿 | `POST /api/v1/agent/runs` with `medical_event_draft_create` |
| 创建提醒 | `POST /api/v1/agent/runs` with `alert_create` |
| 今日健康简报 | `POST /api/v1/agent/runs` with `daily_health_brief` |
| Agent Run 详情 | trace、tool_calls、safety_checks 查询 |

## Agent Run Request

必须支持：

- `target_user_id`
- `family_id`
- `workflow_type`
- `user_message`
- `confirmation`
- `workflow_payload`
- `source`

必须拒绝：

- `tool_name`
- `input_data`

## 错误处理策略

- 使用后端统一错误格式。
- validation error 只展示字段级摘要。
- 403/404 不泄露其他用户或家庭数据存在性。
- 500 不展示 traceback、SQL、本机路径或原始异常细节。

## 脱敏要求

前端 response 展示必须继续隐藏：

- 健康原文长文本
- 文件路径
- 文档抽取全文
- token / password / api key
- traceback / SQL

## 安全文案

前端必须持续强调：

- 根据系统内记录。
- 草稿需要确认。
- 普通健康提醒不是急救。
- 内容不替代医生建议。
