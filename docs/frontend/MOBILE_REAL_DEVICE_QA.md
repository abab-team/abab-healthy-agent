# 移动端真机 QA 记录

Phase 15 的真机 QA 目标是确认 App 在手机上可演示、可理解、可完成核心流程。Codex 可以提供 runbook 和 Web/构建验证，但 Expo Go 扫码、触控体验、不同屏幕尺寸视觉检查需要用户手动完成。

## QA 模式

| 模式 | 目的 | 状态 |
| --- | --- | --- |
| mock mode | 检查 UI、中文文案、页面跳转、空状态与安全边界 | 待用户真机确认 |
| api-auth mode | 连接真实 FastAPI，检查登录和核心链路 | 待用户真机确认 |

## 真机前置条件

- 手机与电脑在同一 Wi-Fi。
- 后端以 `--host 0.0.0.0 --port 8000` 启动。
- 防火墙允许端口 `8000`。
- `EXPO_PUBLIC_API_BASE_URL=http://<电脑局域网IP>:8000`。
- 不使用 `localhost` 或 `127.0.0.1`。

## 必测流程

- [ ] 登录 / logout。
- [ ] 首页概览。
- [ ] 家庭页。
- [ ] 成员详情。
- [ ] AI 管家。
- [ ] daily_health_brief。
- [ ] symptom_draft_create preview / confirm。
- [ ] medical_event_draft_create preview / confirm。
- [ ] alert_create preview / confirm。
- [ ] 文档列表。
- [ ] 文档详情。
- [ ] document processing / OCR preview。
- [ ] OCR 到健康事件草稿 preview / confirm。
- [ ] Agent Run 详情。
- [ ] 设置页。

## 页面体验检查

- [ ] 底部 Tab 不遮挡内容。
- [ ] 页面标题不挤压。
- [ ] 中文不会异常断行或溢出。
- [ ] 卡片不拥挤。
- [ ] 按钮触控区域足够。
- [ ] loading / error / empty 状态清楚。
- [ ] trace id 不撑爆布局。
- [ ] Agent Run 的 tool calls / safety checks 是安全摘要。
- [ ] 页面不暴露 raw 字段、文件路径、token、SQL、traceback。

## 安全文案检查

用户可见文案应强调：

- 根据系统内记录。
- 待确认草稿。
- 写入前需要确认。
- 不替代医生判断或治疗建议。
- 普通健康提醒不是急救服务。

不得出现诱导性医疗结论、处方、剂量、停药建议或自动急救承诺。

## 问题记录模板

| 页面 | 模式 | 设备 | 问题 | 严重级别 | 是否修复 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
|  | mock/api-auth |  |  | P0/P1/P2/P3 |  |  |

