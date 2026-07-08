# Phase 15 Final Review

主题：部署 / 真机 QA / 作品集展示收口。

## 结论

Phase 15 可以视为完成。当前项目达到可演示 MVP 标准：

- 后端本地/局域网演示路径清楚。
- 环境变量和生产安全边界已文档化。
- 移动端真机 QA 清单已补齐。
- Demo 脚本、截图清单和作品集材料已补齐。
- smoke 路径覆盖后端、Auth、Agent、文档处理、OCR 和 RAG。

当前项目仍不是正式生产上线版本。

## 完成内容

- `docs/deployment/MVP_DEPLOYMENT_RUNBOOK.md`
- `docs/deployment/ENVIRONMENT_VARIABLES.md`
- `docs/deployment/PRODUCTION_SAFETY_CHECKLIST.md`
- `docs/deployment/DOCKER_RUNBOOK.md`
- `docs/frontend/MOBILE_REAL_DEVICE_QA.md`
- `docs/frontend/MOBILE_UX_FIX_LOG.md`
- `docs/demo/MVP_DEMO_SCRIPT.md`
- `docs/demo/DEMO_DATA_GUIDE.md`
- `docs/demo/SCREENSHOT_CHECKLIST.md`
- `docs/demo/FEATURE_WALKTHROUGH.md`
- `docs/portfolio/PROJECT_OVERVIEW.md`
- `docs/portfolio/TECHNICAL_HIGHLIGHTS.md`
- `docs/portfolio/ARCHITECTURE_SUMMARY.md`
- `docs/portfolio/INTERVIEW_TALK_TRACK.md`
- `scripts/smoke/deploy_mvp_smoke.ps1`
- `scripts/smoke/mobile_lan_api_smoke.ps1`
- README / mobile README / progress / risk 文档更新。

## 真机 QA 状态

Codex 无法代替用户完成真实手机扫码和触控体验验证。

当前状态：

- Web / smoke 可由 Codex 验证。
- Expo Go 真机 mock mode：待用户手动确认。
- Expo Go 真机 api-auth mode：待用户手动确认。
- 不同屏幕尺寸、中文换行、触控区域、局域网访问、防火墙行为：待用户手动确认。

## 安全边界确认

- 不把项目包装成 AI 医生。
- 不声明具备诊断能力。
- 不输出处方、剂量、停药建议。
- 不承诺自动急救、自动报警、自动联系医院或家人。
- OCR/RAG/LLM 不直接写正式健康事实。
- 写入类 Agent workflow 保持 preview / confirm。
- 前端不开放 `tool_name` / `input_data`。
- 生产前必须关闭 demo header 并设置强密钥。

## 后续建议

1. 用户本人完成真机 QA。
2. 完成录屏和截图。
3. 整理作品集页面。
4. 如继续功能开发，建议进入 Phase 16.A：真实 OCR Provider 受控接入。

