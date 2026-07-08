# Demo 数据说明

Demo 数据由 `backend/scripts/seed_demo_data.py` 生成，并由 `backend/scripts/verify_demo_data.py` 验证。

## 内容范围

Demo 数据包含：

- 3 个 demo 用户。
- 1 个 demo 家庭。
- 家庭成员与共享权限。
- 健康档案。
- 血压记录。
- 症状记录。
- 健康记录草稿。
- 医疗事件。
- 医疗文档 metadata。
- 每日报告。
- 提醒。

## 使用方式

```powershell
$env:PYTHONPATH="backend"
$env:DATABASE_URL="sqlite:///backend/storage/local/demo.sqlite3"
python -m alembic -c backend/alembic.ini upgrade head
python backend/scripts/seed_demo_data.py
python backend/scripts/verify_demo_data.py
```

## Auth demo

Phase 12 之后，demo 用户可用于 auth smoke。demo 密码只用于本地开发验证，不得用于生产。

## 注意事项

- Demo 数据不是医学样本，不代表真实医疗资料。
- Demo 数据只用于演示权限、草稿、文档处理和 Agent 链路。
- 不要把真实用户隐私或真实医疗资料提交到仓库。
- 生产环境不得运行 demo seed。

