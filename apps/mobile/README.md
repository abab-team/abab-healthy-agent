# Family Health Agent Mobile

这是 family-health-agent 的 React Native + Expo 静态 UI 原型，用于 Phase 09.1 移动端信息架构与视觉验证。

当前版本只使用本地 mock 数据，不连接后端 API，不实现登录、LLM、LangGraph、OCR、RAG、上传或推送通知。

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

## Expo Go 预览

```bash
npm start
```

然后用手机上的 Expo Go 扫描终端或浏览器中的二维码。

## 后续接后端 API 的注意事项

如果未来需要让手机访问电脑上运行的后端，手机不能使用 `localhost` 或 `127.0.0.1`。需要使用电脑局域网 IP，例如：

```text
http://192.168.x.x:8000/api/v1
```

当前 Phase 09.1 不实现真实接口调用，只保留静态 UI 与 mock 数据。
