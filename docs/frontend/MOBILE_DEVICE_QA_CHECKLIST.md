# Mobile Device QA Checklist

本文档用于 Phase 09.3.C 的 Expo Go 真机手动视觉 QA。Codex 无法代替用户完成真实手机扫码和触摸走查，但本清单定义了需要验证的步骤与通过标准。

## 准备

1. 手机安装 Expo Go。
2. 手机和电脑连接同一个 Wi-Fi。
3. 电脑进入项目根目录：

```powershell
cd <repo>
```

4. 安装移动端依赖：

```powershell
cd apps/mobile
npm install
```

## Mock Mode 真机检查

Mock mode 不请求后端，适合先确认布局和导航。

```powershell
$env:EXPO_PUBLIC_DATA_MODE="mock"
npx expo start
```

用 Expo Go 扫码后检查：

- 首页。
- 家庭。
- AI 管家。
- 设置。
- 成员详情。
- AI 简报详情。
- Agent Run 详情。
- 创建症状草稿 mock 页。
- 创建提醒 mock 页。

## API Mode 真机检查

真机不能使用 `localhost` 或 `127.0.0.1` 访问电脑后端。需要使用电脑局域网 IP。

示例：

```powershell
$env:EXPO_PUBLIC_DATA_MODE="api"
$env:EXPO_PUBLIC_API_BASE_URL="http://192.168.x.x:8000"
$env:EXPO_PUBLIC_DEMO_USER_ID="<seed 后查询到的 Gala user_id>"
npx expo start
```

后端需要绑定 `0.0.0.0`：

```powershell
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API mode 检查：

- 设置页显示 `Data Mode: api`。
- 设置页显示 API Base URL。
- 设置页显示 `X-Current-User-Id`。
- 设置页 `/health` 状态可刷新。
- 首页家庭成员如来自后端，应显示 API 标识。
- 今日待办、最近动态等聚合缺口应显示 mock / 待接入。
- AI 管家页生成今日健康简报后展示 trace_id。
- Agent Run 详情展示 run / tool calls / safety checks 安全摘要。
- 写入类页面仍显示 mock，不真实提交。

## 如果扫码失败

优先尝试：

```powershell
npx expo start --tunnel
```

还需要检查：

- 电脑和手机是否同一网络。
- Windows 防火墙是否阻止 Expo 或后端端口。
- API Base URL 是否写成电脑局域网 IP。
- 后端是否能在电脑浏览器打开 `/health`。

## UI 走查项

每个页面检查：

- 卡片是否挤压。
- 中文是否换行异常。
- 底部 Tab 是否遮挡内容。
- 页面是否能返回。
- loading / error / empty 是否清楚。
- mock / API / 待接入标识是否清楚。
- 后端不可用时是否显示可理解错误。
- 数据为空时是否显示“系统内暂无相关记录”含义。
- 不把 mock 数据伪装成真实 API 数据。

## 安全文案检查

允许出现：

- 系统内记录。
- 健康简报。
- 待确认草稿。
- 普通健康提醒。
- 家庭共享。
- 不替代医生。
- 提醒不是急救。
- 如有紧急情况请联系医生或当地急救服务。

不得出现：

- AI 医生。
- 诊断结果。
- 确诊。
- 处方。
- 剂量建议。
- 停药建议。
- 自动急救。
- 自动报警。
- 自动联系医院。
- 自动联系家人。
- 不用就医。
- 一定没事。

## 记录模板

```text
设备：
系统版本：
网络：
后端地址：
Data Mode：
Demo User ID：

首页：
家庭页：
成员详情：
AI 管家：
AI 简报：
Agent Run：
设置页：
写入 mock 页面：

发现的问题：
截图：
是否阻塞下一阶段：
```
