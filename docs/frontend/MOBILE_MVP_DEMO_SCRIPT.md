# Mobile MVP Demo Script

本文档用于 Phase 09 移动端 MVP 演示。当前 App 支持 `mock` / `api` 两种模式；`api` 模式仍使用 `X-Current-User-Id` demo header，不是真实 Auth/JWT。

## 启动后端 Smoke 环境

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke/mobile_backend_smoke.ps1
powershell -ExecutionPolicy Bypass -File scripts/smoke/mobile_write_workflows_smoke.ps1
```

脚本验证 `/health`、`daily_health_brief`、三个写入 workflow 的 preview / confirm，以及 run / tool_calls / safety_checks 查询。

## 启动 Mock Mode

```powershell
cd apps/mobile
$env:EXPO_PUBLIC_DATA_MODE="mock"
npm run web
```

mock mode 不请求后端，适合演示页面结构、导航、状态和安全文案。

## 启动 API Mode

Web 本机调试：

```powershell
cd apps/mobile
$env:EXPO_PUBLIC_DATA_MODE="api"
$env:EXPO_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
$env:EXPO_PUBLIC_DEMO_USER_ID="<demo-user-id>"
npm run web
```

Expo Go 真机调试：

```powershell
cd apps/mobile
$env:EXPO_PUBLIC_DATA_MODE="api"
$env:EXPO_PUBLIC_API_BASE_URL="http://192.168.x.x:8000"
$env:EXPO_PUBLIC_DEMO_USER_ID="<demo-user-id>"
npm start
```

真机不能使用 `localhost` 或 `127.0.0.1` 访问电脑后端，必须使用电脑局域网 IP。

## 演示路径

1. 首页查看家庭健康概览、今日待办、AI 简报入口、快捷记录和最近动态。
2. 家庭页查看成员、关系标签、共享状态和邀请入口。
3. 成员详情查看基础信息与系统内健康摘要。
4. AI 管家生成今日健康简报。
5. 创建症状草稿：先 preview，再 confirm，确认后查看 trace。
6. 创建健康事件草稿：先 preview，再 confirm，确认后查看 trace。
7. 创建健康提醒：先 preview，再 confirm，确认后查看 trace。
8. Agent Run 详情查看 workflow、status、tool_calls 与 safety_checks 安全摘要。
9. 设置页查看 data mode、API Base URL、`X-Current-User-Id`、`/health` 状态和真机提示。

## 真机演示检查

- 手机和电脑在同一 Wi-Fi。
- API Base URL 使用电脑局域网 IP。
- 底部 Tab 不遮挡按钮。
- 中文长文本正常换行。
- trace_id 不撑开页面。
- loading / success / error / empty 状态清楚。

## 安全边界

演示只使用“系统内记录”“健康简报”“待确认草稿”“普通健康提醒”“不替代医生”“提醒不是急救”等表达。

不得把系统演示说成医疗诊断、处方、剂量建议、停药建议、自动急救、自动联系医院或自动联系家人。

