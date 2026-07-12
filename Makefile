.PHONY: install lock dev api web migrate test lint typecheck build check up down

install:
	mise install
	mise run install

lock:
	mise run lock

dev:
	@echo "Run 'mise run api' and 'mise run web' in separate terminals."

api:
	mise run api

web:
	mise run web

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

down:
	docker compose down

up:
	docker compose up --build
