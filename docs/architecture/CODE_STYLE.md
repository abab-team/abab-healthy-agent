# 代码风格规范

本文档定义 family-health-agent 项目的基础代码风格。所有实现必须服从 `AGENTS.md`、`CODEX_IMPLEMENTATION_PLAN.md` 和架构设计文档，不得为了风格统一而重构目录结构或提前实现后续 Phase。

## Python 风格

- 目标版本以 `backend/pyproject.toml` 中声明为准。
- 默认使用 `ruff` 做 lint 与 import 排序。
- 默认使用 `black` 或 `ruff format` 做格式化，格式化工具由项目配置统一决定。
- 类型标注应优先写在 service、repository、schema、agent harness、tool、workflow 的公共函数边界。
- 异常类型应使用项目内统一异常，不在 API 层裸抛底层数据库或第三方 SDK 异常。

## TypeScript 风格

- 默认使用 `eslint` 做 lint。
- 默认使用 `prettier` 做格式化。
- 前端 API 类型应优先来自 `packages/shared-types` 或 `packages/api-client`。
- React 组件命名使用 `PascalCase`，hooks 使用 `useXxx`。
- 不允许在前端绕过后端权限边界直接构造敏感数据访问。

## 命名规范

- Python 文件、模块、函数、变量使用 `snake_case`。
- Python 类、Pydantic schema、SQLAlchemy model 使用 `PascalCase`。
- TypeScript 文件按所在框架约定命名；通用工具函数使用 `camelCase`。
- 数据库表名使用复数 `snake_case`。
- 业务模块目录使用领域名，例如 `identity`、`family`、`permissions`、`health_data`。
- Agent 工具函数应表达受控能力，例如 `get_recent_metrics`、`create_symptom_record_draft`。

## Import 规范

- import 顺序为标准库、第三方库、项目内模块。
- 禁止使用通配符 import。
- API 层可以 import schema、service、agent_service，但不应 import repository 或数据库 session。
- Agent tools 可以 import service，不允许 import model、repository 或数据库 session。
- Workflow 可以 import harness、tools、LLM client、schema，不允许直接 import repository。
- 业务模块之间的 import 必须符合 `MODULE_BOUNDARIES.md`。

## 注释规范

- 注释用于解释业务边界、安全原因、复杂规则，不重复描述显而易见的代码。
- 涉及医疗安全、权限、AI 草稿确认、文件路径隐藏的代码，应在关键位置保留简短说明。
- 不使用注释掩盖临时代码；未完成事项必须通过 TODO 标明责任范围和后续 Phase。

## 禁止事项

- 不允许为了格式化而重排目录结构。
- 不允许把业务逻辑写进 API 层。
- 不允许把 Agent、service、repository 混在同一层。
- 不允许在测试中依赖真实 LLM API。
- 不允许把密钥、Token、真实隐私数据写入代码或文档。

