.PHONY: install dev api web test lint typecheck build up down

install:
	corepack enable
	pnpm install
	python -m pip install -e 'services/kinward[dev]'

dev:
	@echo "Run 'make api' and 'make web' in separate terminals."

api:
	uvicorn kinward.app:app --app-dir services/kinward/src --reload --host 0.0.0.0 --port 8000

web:
	pnpm --filter @kinward/web dev

test:
	pytest services/kinward/tests
	pnpm -r test

lint:
	ruff check services/kinward
	pnpm -r lint

typecheck:
	mypy services/kinward/src
	pnpm -r typecheck

build:
	pnpm -r build

down:
	docker compose down

up:
	docker compose up --build
