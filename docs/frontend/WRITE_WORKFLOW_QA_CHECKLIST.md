# Write Workflow QA Checklist

本文档用于 Phase 09.3.E 写入类 Agent workflow 的移动端 QA。当前只验证受控 workflow 入口，不验证正式草稿确认入库。

## Mock Mode 检查

- 首页、家庭页、AI 管家页、设置页可打开。
- `/create-symptom-draft` 显示 mock 静态预览，不请求后端。
- `/create-health-event-draft` 显示健康事件草稿 mock 静态预览，不请求后端。
- `/create-alert` 显示普通健康提醒 mock 静态预览，不请求后端。
- `/drafts` 明确标注草稿列表真实接入后续实现。
- Agent Run 详情只展示安全摘要。

## API Mode Web 检查

准备：

```powershell
cd apps/mobile
$env:EXPO_PUBLIC_DATA_MODE="api"
$env:EXPO_PUBLIC_API_BASE_URL="http://127.0.0.1:<backend-port>"
$env:EXPO_PUBLIC_DEMO_USER_ID="<seed 后查询到的 Gala user_id>"
npm run web
```

检查：

- 设置页 `/health` 可刷新成功。
- AI 管家页可执行 `daily_health_brief`。
- 症状草稿页 preview 不写入，confirm 创建待确认草稿。
- 健康事件草稿页 preview 不写入，confirm 创建待确认草稿。
- 健康提醒页 preview 不写入，confirm 创建普通健康提醒。
- 每次成功后显示 trace_id 的短摘要，并可进入 Agent Run 详情。
- Agent Run 详情展示 workflow_type、status、tool_calls、安全检查摘要。

## API Mode Expo Go 真机检查

- 手机和电脑在同一 Wi-Fi。
- 后端绑定 `0.0.0.0`。
- `EXPO_PUBLIC_API_BASE_URL` 使用电脑局域网 IP。
- 真机不能使用 `localhost` 或 `127.0.0.1`。
- 如扫码失败，可尝试 Expo tunnel。

## Workflow 逐项检查

### symptom_draft_create

- 页面标题使用“症状草稿”。
- preview 显示 `confirmation=false`，不会写入。
- confirm 显示 `confirmation=true`，创建待确认草稿。
- 成功后可跳 Agent Run 详情。

### medical_event_draft_create

- 页面标题使用“健康事件草稿”。
- preview 显示 `confirmation=false`，不会写入。
- confirm 显示 `confirmation=true`，创建待确认草稿。
- 页面不显示原始长文本、文件路径或文档抽取全文。

### alert_create

- 页面标题使用“健康提醒”。
- preview 显示 `confirmation=false`，不会写入。
- confirm 显示 `confirmation=true`，创建普通健康提醒。
- 页面明确提醒不是急救。
- 如遇紧急情况，请联系医生或当地急救服务。

## 错误与安全检查

- safety blocked 必须显示为未写入。
- permission denied 必须显示错误。
- network failed 必须显示错误。
- 后端 400/403/404/500 不得伪装为成功。
- API mode 失败不得自动 fallback mock。

## 不应出现

- 通用 tool execution 入口。
- 页面传 `tool_name` 或 `input_data`。
- 正式草稿确认入库。
- 真实 Auth/JWT。
- LLM、LangGraph、OCR/RAG。
