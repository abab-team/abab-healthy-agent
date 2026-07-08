# MVP 演示部署 Runbook

本文档用于 Phase 15 的最小可演示部署。目标不是正式上云生产，而是让后端、demo 数据、移动端 API 访问和核心 smoke 能稳定复现。

## 部署定位

当前推荐路径：

1. 本地 FastAPI 后端 + SQLite demo DB。
2. 手机与电脑在同一局域网，Expo Go 使用电脑局域网 IP 访问 API。
3. Docker Compose 作为开发/演示环境备选路径。
4. PostgreSQL、对象存储、真实 OCR、真实 embedding、vector DB、云部署留作后续生产化阶段。

## 前置条件

- Python 3.12 或项目可用的 Codex bundled Python。
- Node.js 与 npm，用于移动端 Expo。
- 可选：Docker Desktop，用于 `docker-compose.dev.yml` 演示。
- 手机与电脑连接同一 Wi-Fi。

## 后端本地启动

```powershell
$env:PYTHONPATH="backend"
$env:DATABASE_URL="sqlite:///backend/storage/local/demo.sqlite3"
python -m alembic -c backend/alembic.ini upgrade head
python backend/scripts/seed_demo_data.py
python backend/scripts/verify_demo_data.py
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

验证：

```powershell
curl http://127.0.0.1:8000/health
```

手机访问时不要使用 `localhost` 或 `127.0.0.1`。请使用电脑局域网 IP：

```text
http://<电脑局域网IP>:8000
```

## 移动端连接真实 API

在 `apps/mobile/.env` 中配置：

```text
EXPO_PUBLIC_DATA_MODE=api-auth
EXPO_PUBLIC_API_BASE_URL=http://<电脑局域网IP>:8000
```

如果只做开发 demo，也可以使用 api-demo：

```text
EXPO_PUBLIC_DATA_MODE=api
EXPO_PUBLIC_AUTH_MODE=demo
EXPO_PUBLIC_DEMO_USER_ID=<seed demo user id>
```

运行：

```powershell
cd apps/mobile
npm install
npx expo start
```

用 Expo Go 扫码。真机不能用 `localhost`，防火墙需要允许后端端口 `8000`。

## Docker Compose 路径

```powershell
docker compose -f docker-compose.dev.yml config
docker compose -f docker-compose.dev.yml up --build
```

验证：

```powershell
curl http://127.0.0.1:8000/health
```

停止：

```powershell
docker compose -f docker-compose.dev.yml down
```

当前 Docker 路径用于开发演示，不代表生产部署完成。生产建议使用托管 PostgreSQL、持久化对象存储、明确域名 CORS、HTTPS、日志与备份策略。

## 推荐 smoke 顺序

```powershell
python -m compileall backend/app backend/tests
python -m alembic -c backend/alembic.ini upgrade head
python backend/scripts/seed_demo_data.py
python backend/scripts/verify_demo_data.py
python -m unittest discover backend/tests/api -v
scripts/smoke/mobile_backend_smoke.ps1
scripts/smoke/auth_smoke.ps1
scripts/smoke/document_upload_smoke.ps1
scripts/smoke/document_processing_smoke.ps1
scripts/smoke/ocr_document_smoke.ps1
scripts/smoke/rag_retrieval_smoke.ps1
scripts/smoke/rag_agent_smoke.ps1
```

这些 smoke 会创建临时数据库或本地 storage 产物。验证后必须清理 smoke DB、上传文件、`__pycache__`，不要提交。

## 生产前必须修改

- `AUTH_DEMO_HEADER_ENABLED=false`
- 使用强随机 `JWT_SECRET_KEY` 和 `SECRET_KEY`
- `DEBUG=false`
- `CORS_ORIGINS` 使用明确域名，不使用 `*`
- `DATABASE_URL` 指向持久化 PostgreSQL
- `DOCUMENT_STORAGE_DIR` 或对象存储必须持久化并有访问控制
- `OCR_ENABLED`、`LLM_ENABLED`、`RAG_ENABLED` 默认关闭或受控开启
- 不提交 `.env`、API key、JWT secret、上传文件、smoke DB

