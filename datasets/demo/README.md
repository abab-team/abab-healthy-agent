# Phase 03 Demo 数据说明

本目录记录 `family-health-agent` 的 Phase 03 合成 demo 数据。所有数据只用于本地开发、后续 Service/API/Agent/前端演示和验证，不代表真实医疗资料，也不构成医学诊断、处方建议或用药剂量建议。

## Demo 用户

- Gala：`gala.demo@example.com`，家庭 owner。
- 爸爸：`father.demo@example.com`，家庭成员。
- 妈妈：`mother.demo@example.com`，家庭成员。

手机号使用 `demo_gala_phone`、`demo_father_phone`、`demo_mother_phone` 这类明确 demo 值，不使用真实手机号。

## Demo 家庭结构

家庭名：`Gala 的家庭`

- Gala：`role=owner`，`relationship_label=本人`
- 爸爸：`role=member`，`relationship_label=爸爸`
- 妈妈：`role=member`，`relationship_label=妈妈`

`relationship_label` 是家庭内关系标签，不是用户全局身份。

## Demo 健康数据

- Gala：最近 7 天睡眠、步数、体重、BMI、心率指标。
- 爸爸：最近 30 天 10 条血压记录，最近 3 条略高；少量心率记录；1 条体检事件；1 条资料元信息；血压关注和复查提醒。
- 妈妈：最近 7 天步数记录，最近 2 天略低；2 条症状记录；1 条膝盖不适观察事件；症状随访提醒。
- 家庭权限：3 位成员均有一条 `member_share_permissions`，`share_all=true`，细粒度权限默认开启。
- 日报：Gala、爸爸、妈妈各 1 条今日日报。
- 草稿：1 条爸爸头晕和血压输入的 pending demo 草稿，用于后续确认卡演示；它不是正式健康事实。

## 可演示场景

- 登录或模拟选择 Gala 用户。
- 查看 `Gala 的家庭` 和家庭成员关系。
- 查看家庭共享权限基础数据。
- 查看爸爸最近血压记录。
- 查看妈妈膝盖疼症状和步数变化。
- 查看 Gala 自己的睡眠、步数、体重、BMI、心率。
- 查看 3 位成员的今日日报。
- 查看爸爸血压关注提醒、爸爸复查提醒、妈妈症状随访提醒。
- 后续 Agent 可基于这些数据回答“我爸最近血压怎么样？”。
- 后续确认卡可基于 pending 草稿演示“爸爸晚上有点头晕，血压145/92”。

## 运行 Seed

先确保数据库迁移已经到最新版本：

```bash
python -m alembic -c backend/alembic.ini upgrade head
```

然后运行：

```bash
python backend/scripts/seed_demo_data.py
```

脚本会读取项目环境中的 `DATABASE_URL`。它只清理固定 demo 用户和 `Gala 的家庭` 相关数据，再重建 demo 数据；重复执行不会累计重复数据。

## 验证 Demo 数据

```bash
python backend/scripts/verify_demo_data.py
```

验证脚本会检查 demo 用户、家庭、成员、权限、健康档案、爸爸血压、妈妈症状、日报和提醒的数量。

## 安全声明

- 全部 demo 数据均为合成数据。
- `file_path` 使用 `demo://` 前缀，不指向本机真实路径。
- 不包含真实 API key、GitHub PAT、数据库密钥或个人隐私。
- 文案只描述系统内 demo 记录，不表示现实健康结论。
- 不包含诊断、处方建议或药物剂量建议。
