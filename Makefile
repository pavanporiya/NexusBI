.PHONY: help dev down test lint format clean db-migrate db-revision

help:
	@echo "NexusBI Development Command Interface"
	@echo "======================================"
	@echo "dev          - Start PostgreSQL, Redis, and Backend local containers"
	@echo "down         - Stop local development containers"
	@echo "test         - Run backend and frontend test suites"
	@echo "lint         - Run linting checks (Ruff, ESLint)"
	@echo "format       - Apply formatting rules (Black, Prettier)"
	@echo "clean        - Remove caches and build artifacts"
	@echo "db-migrate   - Run Alembic database migrations"
	@echo "db-revision  - Create a new Alembic database migration file"

dev:
	docker compose -f deployment/docker-compose.yml up --build

down:
	docker compose -f deployment/docker-compose.yml down

test:
	cd backend && uv run pytest
	cd frontend && npm run test

lint:
	cd backend && uv run ruff check .
	cd backend && uv run mypy .
	cd frontend && npm run lint

format:
	cd backend && uv run ruff format .
	cd frontend && npm run format

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf frontend/.next frontend/out

db-migrate:
	cd backend && uv run alembic upgrade head

db-revision:
	@read -p "Enter migration message: " msg; \
	cd backend && uv run alembic revision --autogenerate -m "$$msg"
