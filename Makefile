# =========================================================
# Abab Healthy Agent 开发命令入口
# 说明：
# 1. Makefile 用来把常用命令封装成 make xxx。
# 2. 这样你不用每次手写 docker compose、uvicorn、alembic 等长命令。
# 3. 当前命令主要覆盖：启动、测试、语法检查、迁移、seed、验证 demo 数据。
# =========================================================


# =========================================================
# 全局变量
# =========================================================

# Docker Compose 命令
# -f docker-compose.dev.yml 表示使用开发环境的 compose 配置文件
# 后面执行 $(COMPOSE) up --build，就等价于：
# docker compose -f docker-compose.dev.yml up --build
COMPOSE := docker compose -f docker-compose.dev.yml

# Python 命令
# ?= 表示：如果外部没有传 PYTHON，就默认使用 python
# 例如：
# make test PYTHON=python3
# 可以临时改成 python3
PYTHON ?= python
ENV_FILE ?= .env


# =========================================================
# 声明伪目标
# =========================================================
# .PHONY 表示这些名字不是实际文件名，而是 make 命令名。
# 否则如果目录里刚好有一个叫 test 的文件，make test 可能会被误判为已完成。
.PHONY: help dev backend-dev test lint format migrate seed verify-demo production-check production-smoke


# =========================================================
# 帮助命令
# 用法：
# make help
# =========================================================

help:
	@echo "family-health-agent development commands"
	@echo "  make dev          - start backend, postgres, redis, and minio with Docker Compose"
	@echo "  make backend-dev  - start the FastAPI backend directly on the host"
	@echo "  make test         - run the Phase 01 backend smoke test"
	@echo "  make lint         - run Python syntax checks"
	@echo "  make format       - run Python compile checks as a formatting placeholder"
	@echo "  make migrate      - run Alembic migrations to head"
	@echo "  make seed         - seed deterministic Phase 03 demo data"
	@echo "  make verify-demo  - verify Phase 03 demo data"
	@echo "  make production-check ENV_FILE=.env - run Phase 26 production readiness checks"
	@echo "  make production-smoke - run Phase 26 production readiness smoke"


# =========================================================
# 启动完整开发环境
# 用法：
# make dev
#
# 作用：
# 使用 docker-compose.dev.yml 启动开发环境。
# 通常包括：
# - backend 后端服务
# - postgres 数据库
# - redis 缓存
# - minio 对象存储
#
# --build 表示启动前重新构建镜像。
# =========================================================

dev:
	$(COMPOSE) up --build


# =========================================================
# 只在本机启动后端
# 用法：
# make backend-dev
#
# 作用：
# 不通过 Docker 启动后端，而是在本机直接运行 FastAPI。
#
# 命令解释：
# cd backend
#   进入 backend 目录
#
# python -m uvicorn app.main:app
#   使用 uvicorn 启动 FastAPI 应用
#
# app.main:app
#   表示读取 backend/app/main.py 里的 app 对象
#
# --host 0.0.0.0
#   允许局域网或容器访问，不只绑定 127.0.0.1
#
# --port 8000
#   后端服务端口是 8000
#
# --reload
#   代码变化后自动重启，适合开发环境
# =========================================================

backend-dev:
	cd backend && $(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload


# =========================================================
# 后端冒烟测试
# 用法：
# make test
#
# 当前作用：
# 只测试 /health 接口是否可用。
#
# 这个测试很轻量，不等于完整单元测试。
# 它主要验证：
# 1. FastAPI 应用可以被导入
# 2. /health 路由存在
# 3. 返回状态码是 200
# 4. 返回内容符合预期
# =========================================================

test:
	cd backend && $(PYTHON) -c "from fastapi.testclient import TestClient; from app.main import app; response = TestClient(app).get('/health'); assert response.status_code == 200; assert response.json() == {'status': 'ok', 'service': 'family-health-agent'}; print('health smoke test passed')"


# =========================================================
# Python 语法检查
# 用法：
# make lint
#
# 当前作用：
# 使用 python -m compileall app 编译 app 目录下的 Python 文件。
#
# 注意：
# 这只是“语法级检查”，不是严格意义上的 lint。
# 它能发现：
# - 语法错误
# - import 阶段的部分问题
#
# 它不能替代：
# - ruff
# - mypy
# - pytest
# - black
# =========================================================

lint:
	cd backend && $(PYTHON) -m compileall app


# =========================================================
# 格式化占位命令
# 用法：
# make format
#
# 当前作用：
# 现在和 make lint 一样，只是跑 compileall。
#
# 注意：
# 这不是实际格式化。
# 后续如果接入 ruff / black，可以改成：
# cd backend && ruff format .
# 或：
# cd backend && black .
# =========================================================

format:
	cd backend && $(PYTHON) -m compileall app


# =========================================================
# 数据库迁移
# 用法：
# make migrate
#
# 作用：
# 使用 Alembic 把数据库结构升级到最新版本。
#
# 命令解释：
# cd backend
#   进入后端目录
#
# python -m alembic -c alembic.ini upgrade head
#   使用 backend/alembic.ini 配置文件执行迁移
#   upgrade head 表示迁移到最新版本
#
# 前提：
# 1. PostgreSQL 已启动
# 2. DATABASE_URL 配置正确
# 3. alembic/versions 下迁移文件没有错误
# =========================================================

migrate:
	cd backend && $(PYTHON) -m alembic -c alembic.ini upgrade head


# =========================================================
# 写入 demo 数据
# 用法：
# make seed
#
# 作用：
# 运行 backend/scripts/seed_demo_data.py。
#
# 预期用途：
# 给开发环境写入固定的演示数据，例如：
# - demo 用户
# - 家庭
# - 家庭成员
# - 权限
# - 健康数据
#
# 前提：
# 1. 数据库已启动
# 2. 已执行 make migrate
# 3. seed_demo_data.py 代码可用
# =========================================================

seed:
	$(PYTHON) backend/scripts/seed_demo_data.py


# =========================================================
# 验证 demo 数据
# 用法：
# make verify-demo
#
# 作用：
# 运行 backend/scripts/verify_demo_data.py。
#
# 预期用途：
# 检查 seed 是否真的写入成功，例如：
# - demo 用户是否存在
# - 家庭是否存在
# - 家庭成员关系是否存在
# - 血压等健康数据是否存在
#
# 前提：
# 1. 数据库已启动
# 2. 已执行 make migrate
# 3. 已执行 make seed
# =========================================================

verify-demo:
	$(PYTHON) backend/scripts/verify_demo_data.py

production-check:
	$(PYTHON) tools/check_production_readiness.py --env-file $(ENV_FILE)

production-smoke:
	powershell -ExecutionPolicy Bypass -File scripts/smoke/production_readiness_smoke.ps1 -Python $(PYTHON)
