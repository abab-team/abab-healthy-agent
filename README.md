# Family Health Agent

Family Health Agent 是一个面向家庭长期使用的健康档案、家庭健康共享与 AI 健康管家系统。项目当前处于 Phase 00：仓库与工程规范阶段，只提供成品级目录骨架和工程约束，不包含可运行后端实现。

## 项目定位

本项目用于管理长期健康档案、健康指标、血压记录、症状随手记、医疗事件时间线、资料中心、日报提醒与受控 AI 管家能力。

医疗边界：系统只做生活健康管理、资料整理、趋势提醒和就医沟通辅助，不做医学诊断、不做处方建议、不做药物剂量建议，也不替代医生。

## 架构原则

- Monorepo。
- 模块化单体后端。
- 多前端入口预留。
- Agent Core 独立域。
- 业务事实归 `backend/app/modules/`。
- Agent 不直接访问数据库，只能通过受控工具调用业务 service。
- 家人数据访问必须经过家庭与权限检查。
- AI 草稿必须用户确认后才能写入正式健康档案。

## 目录结构

```text
family-health-agent/
├─ apps/
├─ backend/
├─ packages/
├─ infra/
├─ docs/
├─ prompts/
├─ datasets/
├─ tools/
├─ docker-compose.yml
├─ docker-compose.dev.yml
├─ .env.example
├─ README.md
└─ Makefile
```

后端核心结构：

```text
backend/
├─ app/
│  ├─ core/
│  ├─ db/
│  ├─ api/
│  ├─ modules/
│  ├─ agent/
│  ├─ integrations/
│  ├─ jobs/
│  ├─ workers/
│  ├─ common/
│  └─ utils/
├─ alembic/
├─ tests/
├─ scripts/
└─ storage/
```

## 开发阶段

开发必须严格按 `CODEX_IMPLEMENTATION_PLAN.md` 的 Phase 顺序执行：

```text
Phase 00: 仓库与工程规范
Phase 01: 后端基础设施
Phase 02: 数据库模型与 Alembic
Phase 03: Seed Demo Data
Phase 04: 核心业务模块 Service 层
Phase 05: 基础 API 层
Phase 06: 权限系统闭环
Phase 07: Health Agent Harness
Phase 08: Agent Tools
Phase 09: LLM Client 与 Prompt 管理
Phase 10: LangGraph Workflows
Phase 11: 日报与提醒系统
Phase 12: 文档中心与资料处理
Phase 13: 知识库 / RAG
Phase 14: 导出与分享
Phase 15: Web 前端
Phase 16: 测试体系
Phase 17: 部署与运维
Phase 18: 移动端 / 设备 / 通知扩展
```

当前阶段不启动 FastAPI、不创建数据库模型、不写业务代码。

## 如何阅读实施计划

开始任何开发前先阅读：

1. `AGENTS.md`
2. `CODEX_IMPLEMENTATION_PLAN.md`
3. `docs/architecture/CODEX_IMPLEMENTATION_PLAN_v1.0.md`
4. `docs/architecture/家庭健康Agent_项目架构设计_v1.0.md`
5. `docs/architecture/DEVELOPMENT_RULES.md`
6. `docs/architecture/MODULE_BOUNDARIES.md`
7. `docs/architecture/NO_GO_RULES.md`

阅读顺序以项目约束和安全边界为先，再执行对应 Phase 的任务。不得提前实现后续 Phase。

## 本地命令

当前 Makefile 只提供占位命令：

```text
make help
make dev
make test
make lint
make format
```

这些命令暂不启动真实服务；Phase 01 后再接入后端启动、测试和检查逻辑。
