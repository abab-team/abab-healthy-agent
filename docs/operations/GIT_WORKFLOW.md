# Git 工作流

本文档定义 family-health-agent 的 Git 使用规范。所有提交必须遵守 `AGENTS.md`、`CODEX_IMPLEMENTATION_PLAN.md` 和工程规则文档。

## 分支规范

- `main` 是主分支，保持可追踪、可审查。
- 功能开发建议使用 `feature/<phase>-<topic>`。
- 修复建议使用 `fix/<topic>`。
- 文档建议使用 `docs/<topic>`。
- 实验性工作不得直接进入 `main`，除非项目负责人明确要求。

## Commit Message 规范

提交信息使用简短英文 conventional commit 风格：

```text
docs: add project engineering rules
feat: add health data service
fix: enforce member permission check
test: add permission service tests
chore: update tooling config
```

要求：

- 一个 commit 聚焦一个任务。
- 不把无关格式化、目录调整和功能实现混在一起。
- 不提交密钥、Token、真实隐私数据。
- 不用含糊信息，例如 `update`、`fix bug`、`misc`。

## 提交前检查

提交前必须执行：

```text
git status --short --branch
```

并根据变更类型运行检查：

- 文档变更：检查 Markdown 文件存在、内容可读、路径正确。
- Python 变更：运行相关 lint、typecheck 或 `pytest`。
- 前端变更：运行 lint、typecheck、test 或 build。
- 数据库变更：运行 migration 相关检查。
- Agent 变更：运行权限、工具门禁、Safety、未确认不写入相关测试。

测试失败必须先修复再提交。外部环境导致无法验证时，必须在任务汇报中说明。

## PR 检查清单

提交 PR 前确认：

- 是否只实现当前 Phase 和当前任务。
- 是否没有改动无关架构文档。
- 是否没有重构顶层目录结构。
- API 层是否仍然保持 thin controller。
- Agent 是否没有直接访问数据库。
- LLM 是否没有决定 `current_user_id`、`family_id`、`target_user_id`。
- 写入健康档案是否需要用户确认。
- 家人数据访问是否经过权限检查。
- 健康输出是否遵守医疗安全边界。
- 测试或检查是否已运行并记录结果。
- 是否没有提交密钥、Token、真实隐私数据。

## 冲突处理

- 不使用破坏性命令覆盖他人改动。
- 遇到冲突时先理解双方修改意图，再做最小合并。
- 不为了合并方便删除用户或其他开发者的工作。
- 如冲突涉及架构边界、权限系统或医疗安全，必须先暂停并确认。

