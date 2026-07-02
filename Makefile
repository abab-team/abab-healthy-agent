COMPOSE := docker compose -f docker-compose.dev.yml
PYTHON ?= python

.PHONY: help dev backend-dev test lint format migrate

help:
	@echo "family-health-agent development commands"
	@echo "  make dev          - start backend, postgres, redis, and minio with Docker Compose"
	@echo "  make backend-dev  - start the FastAPI backend directly on the host"
	@echo "  make test         - run the Phase 01 backend smoke test"
	@echo "  make lint         - run Python syntax checks"
	@echo "  make format       - run Python compile checks as a formatting placeholder"
	@echo "  make migrate      - run Alembic migrations to head"

dev:
	$(COMPOSE) up --build

backend-dev:
	cd backend && $(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	cd backend && $(PYTHON) -c "from fastapi.testclient import TestClient; from app.main import app; response = TestClient(app).get('/health'); assert response.status_code == 200; assert response.json() == {'status': 'ok', 'service': 'family-health-agent'}; print('health smoke test passed')"

lint:
	cd backend && $(PYTHON) -m compileall app

format:
	cd backend && $(PYTHON) -m compileall app

migrate:
	cd backend && $(PYTHON) -m alembic -c alembic.ini upgrade head
