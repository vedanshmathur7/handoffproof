.PHONY: setup deps-up deps-down backend-dev frontend-dev backend-test backend-lint backend-typecheck backend-check frontend-test frontend-lint frontend-typecheck frontend-build frontend-check test lint typecheck build check demo

setup:
	cd backend && uv sync
	cd frontend && npm install

deps-up:
	docker compose up -d --wait postgres

deps-down:
	docker compose down

backend-dev:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

frontend-dev:
	cd frontend && npm run dev

backend-test:
	cd backend && uv run pytest

backend-lint:
	cd backend && uv run ruff check .

backend-typecheck:
	cd backend && uv run mypy

backend-check: backend-test backend-lint backend-typecheck

frontend-test:
	cd frontend && npm test

frontend-lint:
	cd frontend && npm run lint

frontend-typecheck:
	cd frontend && npm run typecheck

frontend-build:
	cd frontend && npm run build

frontend-check: frontend-test frontend-lint frontend-typecheck frontend-build

test: backend-test frontend-test

lint: backend-lint frontend-lint

typecheck: backend-typecheck frontend-typecheck

build: frontend-build

check: backend-check frontend-check

demo:
	@echo "Demo data is introduced in Task 02."
