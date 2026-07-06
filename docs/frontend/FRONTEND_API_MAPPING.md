# Frontend API Mapping

本文档记录 Phase 09 前端与后端 API 的对接计划。Phase 09.2 只准备 API 契约、mock API 与交互状态，不请求真实后端。

## Phase 09.2 状态

- 当前移动端仍使用 `apps/mobile/lib/mockApi.ts`。
- 当前移动端新增 `apps/mobile/types/api.ts` 作为 TypeScript API 契约草案。
- 当前不创建真实 API client。
- 当前不调用 `fetch` / `axios` 请求 FastAPI。
- 当前不实现 Auth/JWT。
- 当前不调用 LLM、LangGraph、OCR/upload/RAG。

## Phase 09.3 接入原则

Phase 09.3 才允许把 `mockApi` 替换或包裹为真实 FastAPI 请求。

真机访问本机后端时不能使用 `localhost` 或 `127.0.0.1`，应使用电脑局域网 IP，例如：

```text
http://192.168.x.x:8000/api/v1
```

当前后端仍使用开发调试身份入口：

```text
X-Current-User-Id: <demo_user_id>
```

该 header 只用于开发调试，不是正式 Auth/JWT。

## 页面到 API 的映射草案

| 页面 | Phase 09.2 mock 方法 | Phase 09.3 预期 API |
| --- | --- | --- |
| 首页 | `getCurrentUser`, `getFamilyOverview`, `getAgentBrief` | identity / family / agent runs |
| 家庭页 | `getFamilyOverview`, `getMemberDetail` | family member APIs |
| 成员详情 | `getMemberDetail` | family member profile / health summary APIs |
| 草稿页 | `getDrafts`, `updateDraftStatus` | health record draft APIs |
| 创建症状草稿 | `createSymptomDraftPreview`, `createSymptomDraftConfirmed` | `POST /api/v1/agent/runs` |
| 创建健康事件草稿 | mock local state | `POST /api/v1/agent/runs` |
| 创建提醒 | `createAlertPreview`, `createAlertConfirmed` | `POST /api/v1/agent/runs` |
| 今日健康简报 | `getAgentBrief` | `POST /api/v1/agent/runs` |
| Agent Run 详情 | `getAgentRun` | Agent trace / tool-calls / safety-checks APIs |

## Agent Workflow Confirmation

Agent API 只允许白名单 workflow：

- `daily_health_brief`
- `symptom_draft_create`
- `medical_event_draft_create`
- `alert_create`

前端交互规则：

- preview：`confirmation=false`
- confirm：`confirmation=true`

前端不得开放：

- `tool_name`
- `input_data`
- 通用 tool execution

## Response 安全要求

前端不得展示：

- `raw_text`
- `file_path`
- `raw_extracted_text`
- token / password / api key
- traceback / SQL
- 过长敏感原文

无记录时应写“系统内暂无相关记录”，不能写成现实身体结论。
