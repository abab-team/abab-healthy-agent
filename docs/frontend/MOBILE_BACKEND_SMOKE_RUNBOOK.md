# Mobile Backend Smoke Runbook

本文档用于 Phase 09.3.B 前后端联调 smoke。目标是验证移动端 Phase 09.3.A 已接入的只读 API、`/health` 与 `daily_health_brief`，不接入写入类 workflow。

## 当前结论

本次本机验证结果：

- 系统 Python 3.11 的 `pip` 损坏，错误为 `No module named 'pip._vendor.rich.console'`。
- Docker CLI 存在，但 Docker Desktop Linux engine 未运行，`docker compose up -d postgres` 无法启动 PostgreSQL。
- 使用 Codex bundled Python 创建临时 `.venv-smoke`，直接安装 `backend/pyproject.toml` 中的依赖列表后，可完成 smoke。
- `pip install -e backend` 当前会被 setuptools flat-layout package discovery 拦截，原因是 `backend` 下同时存在 `app`、`alembic`、`storage` 顶层目录；这是 packaging 元数据问题，不影响按依赖运行后端。
- 使用临时 SQLite smoke DB 可完成 Alembic migration、demo seed、demo verify、`GET /health`、`daily_health_brief`、run/tool_calls/safety_checks 查询。

本阶段未修改后端业务代码、后端 API、模型或 migration。

## 推荐路径 A：Docker/PostgreSQL

在项目根目录执行：

```powershell
cd <repo>
copy .env.example .env
docker compose -f docker-compose.dev.yml up -d postgres
```

确认 `.env` 中：

```text
DATABASE_URL=postgresql+psycopg://family_health:family_health@localhost:5432/family_health
```

创建并激活虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install "alembic>=1.16.0" "fastapi>=0.116.0,<0.117.0" "httpx>=0.28.0" "psycopg[binary]>=3.2.0" "pydantic-settings>=2.10.0" "SQLAlchemy>=2.0.0" "uvicorn[standard]>=0.35.0"
```

迁移与 demo 数据：

```powershell
python -m alembic -c backend/alembic.ini upgrade head
python backend/scripts/seed_demo_data.py
python backend/scripts/verify_demo_data.py
```

启动 FastAPI：

```powershell
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

验证 `/health`：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

预期：

```json
{"status":"ok","service":"family-health-agent"}
```

## 备用路径 B：Codex bundled Python + SQLite Smoke DB

当系统 `pip` 损坏或 Docker Desktop 不可用时，可用此路径完成本地 smoke。该路径只用于联调验证，不代表生产数据库方案。

```powershell
cd <repo>
& "<codex-bundled-python>" -m venv .venv-smoke
.\.venv-smoke\Scripts\python.exe -m pip install "alembic>=1.16.0" "fastapi>=0.116.0,<0.117.0" "httpx>=0.28.0" "psycopg[binary]>=3.2.0" "pydantic-settings>=2.10.0" "SQLAlchemy>=2.0.0" "uvicorn[standard]>=0.35.0"
```

创建临时 SQLite smoke DB：

```powershell
$env:DATABASE_URL="sqlite:///./backend/storage/smoke_phase_09_3_b.db"
.\.venv-smoke\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
.\.venv-smoke\Scripts\python.exe backend/scripts/seed_demo_data.py
.\.venv-smoke\Scripts\python.exe backend/scripts/verify_demo_data.py
```

## 获取 Demo User UUID

不要在前端硬编码 UUID。seed 后用只读查询获取：

```powershell
$env:DATABASE_URL="sqlite:///./backend/storage/smoke_phase_09_3_b.db"
$env:PYTHONPATH="backend"
@'
from sqlalchemy import select
from app.db.session import SessionLocal
from app.modules.identity.models import User
from app.modules.family.models import Family
with SessionLocal() as session:
    for user in session.scalars(select(User).order_by(User.email)):
        print(f"USER {user.email} {user.id}")
    for family in session.scalars(select(Family)):
        print(f"FAMILY {family.name} {family.id}")
'@ | .\.venv-smoke\Scripts\python.exe -
```

本次 smoke 示例输出：

```text
USER father.demo@example.com 5db95d9b-4303-4833-a92b-abedf437495d
USER gala.demo@example.com 99154c5b-6df9-437f-8ad7-d532ce6a231c
USER mother.demo@example.com 1d04051b-8132-4d3e-8e6f-6548495138b1
FAMILY Gala 的家庭 e6dd1318-1f7f-4e16-b2f7-38b8c813a90b
```

这些值来自本地 seed 后的 smoke DB，不能作为长期固定值写入移动端代码。

## daily_health_brief Smoke

启动后端时使用绝对 SQLite URL，避免相对路径随工作目录变化：

```powershell
$db = (Resolve-Path "backend\storage\smoke_phase_09_3_b.db").Path -replace "\\","/"
$env:DATABASE_URL="sqlite:///$db"
$env:PYTHONPATH="backend"
cd backend
..\.venv-smoke\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 18001
```

另开终端调用：

```powershell
$headers = @{
  "X-Current-User-Id" = "99154c5b-6df9-437f-8ad7-d532ce6a231c"
  "Content-Type" = "application/json"
}

$body = @{
  target_user_id = "99154c5b-6df9-437f-8ad7-d532ce6a231c"
  workflow_type = "daily_health_brief"
  user_message = "请根据系统内记录生成今日健康简报。"
  source = "phase_09_3_b_smoke"
} | ConvertTo-Json

$run = Invoke-RestMethod -Uri "http://127.0.0.1:18001/api/v1/agent/runs" -Method Post -Headers $headers -Body $body
$run.trace_id
```

只允许 `workflow_type=daily_health_brief`。不要传 `tool_name`，不要传 `input_data`。

继续查询：

```powershell
$traceId = $run.trace_id
Invoke-RestMethod -Uri "http://127.0.0.1:18001/api/v1/agent/runs/$traceId" -Headers $headers
Invoke-RestMethod -Uri "http://127.0.0.1:18001/api/v1/agent/runs/$traceId/tool-calls" -Headers $headers
Invoke-RestMethod -Uri "http://127.0.0.1:18001/api/v1/agent/runs/$traceId/safety-checks" -Headers $headers
```

本次验证结果：

- `/health`：200。
- `daily_health_brief`：`completed`。
- `tool_calls`：5 条。
- `safety_checks`：2 条。

## 移动端 API Mode

Web 本机预览可使用：

```powershell
cd apps/mobile
$env:EXPO_PUBLIC_DATA_MODE="api"
$env:EXPO_PUBLIC_API_BASE_URL="http://127.0.0.1:18001"
$env:EXPO_PUBLIC_DEMO_USER_ID="99154c5b-6df9-437f-8ad7-d532ce6a231c"
npm run web
```

检查：

- 设置页显示 `Data Mode: api`。
- 设置页显示 API Base URL。
- 设置页显示 `X-Current-User-Id`。
- 设置页 `/health` 状态为后端返回。
- AI 管家页只触发 `daily_health_brief`。
- Agent Run 详情只展示安全摘要。

写入类页面仍为 mock：

- 创建症状草稿。
- 创建健康事件草稿。
- 创建提醒。
- 草稿确认/修改/暂不处理。

## Expo Go 真机预览

手机不能使用 `localhost` 或 `127.0.0.1` 访问电脑后端。需要：

- 手机与电脑在同一网络。
- 使用电脑局域网 IP，例如 `http://192.168.x.x:8000`。
- 后端绑定 `0.0.0.0`，例如 `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`。

移动端环境变量示例：

```text
EXPO_PUBLIC_DATA_MODE=api
EXPO_PUBLIC_API_BASE_URL=http://192.168.x.x:8000
EXPO_PUBLIC_DEMO_USER_ID=<seed 后查询到的 Gala user_id>
```

真机视觉 QA 详见：

```text
docs/frontend/MOBILE_DEVICE_QA_CHECKLIST.md
```

## 常见问题

### pip 损坏

错误：

```text
No module named 'pip._vendor.rich.console'
```

说明：这是本机 Python / pip 环境损坏，不是项目代码问题。可选处理：

- 用 `python -m ensurepip --upgrade` 修复系统 pip。
- 使用项目虚拟环境。
- 使用 Codex bundled Python 创建 `.venv-smoke`。

### Docker Desktop 未运行

错误：

```text
open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified
```

说明：Docker CLI 存在，但 Docker Desktop Linux engine 未启动。启动 Docker Desktop 后重试 PostgreSQL 路径，或使用 SQLite smoke 路径。

### demo user id 不匹配

症状：

- `X-Current-User-Id` 返回 404/403。
- Agent run 无法访问家庭数据。

处理：

- 重新运行 seed。
- 用上文查询脚本读取当前数据库内的 user_id / family_id。
- 不要把旧 smoke DB 的 UUID 当成固定值。

### localhost 真机不可访问

Expo Go 真机访问电脑后端时，`localhost` 指向手机自己。必须使用电脑局域网 IP。
