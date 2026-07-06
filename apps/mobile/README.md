# Family Health Agent Mobile

这是 family-health-agent 的 React Native + Expo 移动端原型。Phase 09.3.A 开始加入可切换 API Client，用于只读 demo 数据与 `daily_health_brief` 联调。

默认版本仍使用本地 mock 数据。只有在显式设置 `EXPO_PUBLIC_DATA_MODE=api` 后，才会请求 FastAPI。

当前仍不实现真实登录、Auth/JWT、LLM、LangGraph、OCR、RAG、上传或推送通知。

## 页面范围

- 首页：家庭今日概览、今日待办、AI 今日简报、快速记录、最近动态。
- 家庭：家庭卡片、成员列表、共享权限概览、邀请成员入口。
- AI 管家：安全提示、推荐动作、待确认草稿、AI 执行记录、Trace 调试摘要。
- 设置：用户卡片、个人资料、通知、家庭共享、隐私、数据来源、开发者调试、关于 App。

二级静态页面：

- `/member/[id]`
- `/drafts`
- `/agent-brief`
- `/create-symptom-draft`
- `/create-alert`
- `/agent-run/[id]`

## 本地运行

```bash
npm install
npm run web
```

也可以直接运行：

```bash
npx expo start --web
```

## 数据模式与环境变量

复制 `.env.example` 为本地 `.env` 后按需配置：

```text
EXPO_PUBLIC_DATA_MODE=mock
EXPO_PUBLIC_API_BASE_URL=
EXPO_PUBLIC_DEMO_USER_ID=
```

字段说明：

- `EXPO_PUBLIC_DATA_MODE=mock`：默认模式，不请求后端。
- `EXPO_PUBLIC_DATA_MODE=api`：请求 FastAPI，只接入只读 demo API、`GET /health` 与 `daily_health_brief`。
- `EXPO_PUBLIC_API_BASE_URL`：FastAPI 地址，例如 Web 本机调试可用 `http://localhost:8000`。
- `EXPO_PUBLIC_DEMO_USER_ID`：开发调试用户 ID，会作为 `X-Current-User-Id` header 发送。

手机真机访问电脑后端时不能使用 `localhost` 或 `127.0.0.1`，需要使用电脑局域网 IP，例如：

```text
http://192.168.x.x:8000
```

## Phase 09.3.A API 范围

已接入：

- `GET /health`
- `GET /api/v1/families`
- `GET /api/v1/families/{family_id}/members`
- 部分家庭成员健康档案、血压、症状摘要、提醒只读接口
- `POST /api/v1/agent/runs`，但仅用于 `workflow_type=daily_health_brief`
- Agent run / tool-calls / safety-checks 安全摘要查询

仍保持 mock：

- 创建症状草稿
- 创建健康事件草稿
- 创建提醒
- 草稿确认、修改、暂不处理
- 今日待办、最近动态等聚合数据

移动端不会开放通用 tool execution，不允许用户直接传 `tool_name` 或 `input_data`。

## Expo Go 预览

```bash
npm start
```

然后用手机上的 Expo Go 扫描终端或浏览器中的二维码。

## 安全边界

移动端文案必须保持“根据系统内记录”“不替代医生诊断或治疗建议”“普通提醒不是急救服务”。当前不接 LLM，不实现 LangGraph，不实现 OCR/upload/RAG，不实现真实 Auth/JWT。
