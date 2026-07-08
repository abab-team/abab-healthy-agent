# Docker 开发演示 Runbook

本文档说明当前 Docker Compose 路径。它用于开发/演示验证，不代表生产部署完成。

## 配置检查

```powershell
docker compose -f docker-compose.dev.yml config
```

如果 Docker Desktop engine 未运行，上述命令可能失败。请先启动 Docker Desktop。

## 启动

```powershell
docker compose -f docker-compose.dev.yml up --build
```

服务：

- `backend`: FastAPI, port `8000`
- `postgres`: PostgreSQL, port `5432`
- `redis`: Redis, port `6379`
- `minio`: MinIO, ports `9000/9001`

## 验证

```powershell
curl http://127.0.0.1:8000/health
```

进入 backend 容器或本机环境后运行：

```powershell
python -m alembic -c backend/alembic.ini upgrade head
python backend/scripts/seed_demo_data.py
python backend/scripts/verify_demo_data.py
```

## 停止

```powershell
docker compose -f docker-compose.dev.yml down
```

如需要清理卷：

```powershell
docker compose -f docker-compose.dev.yml down -v
```

清理卷会删除 PostgreSQL、Redis、MinIO 数据，仅在确认不需要保留 demo 数据时使用。

## 生产差异

生产部署不应直接复用开发默认值。至少需要：

- 强随机密钥
- 关闭 demo header
- 明确 CORS 域名
- 持久化数据库和对象存储
- HTTPS 与日志/监控
- 文件安全策略

