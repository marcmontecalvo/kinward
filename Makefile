.PHONY: install lock dev api worker migrate test lint typecheck build check smoke up down

install:
	mise install
	mise run install

lock:
	mise run lock

dev:
	@echo "Run 'mise run api' in a terminal."

api:
	mise run api

worker:
	mise run worker

migrate:
	mise run migrate

test:
	mise run test

lint:
	mise run lint

typecheck:
	mise run typecheck

build:
	mise run build

check:
	mise run check

smoke:
	bash scripts/compose-smoke.sh

down:
	docker compose down

up:
	docker compose up --build
