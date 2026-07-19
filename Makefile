.PHONY: install lock dev api worker migrate test lint typecheck build check smoke smoke-ha smoke-peers setup up down new-visual-pack

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

smoke-ha:
	bash scripts/ha-dev-smoke.sh

smoke-peers:
	bash scripts/optional-peers-smoke.sh

# Interactive first-run wizard: choose Honcho/LLM-Wiki/HA-dev, bring the stack
# up, and mint a Home Assistant integration token. The household itself is
# bootstrapped later, from the Kinward integration's own setup step in HA.
setup:
	bash scripts/kinward-setup.sh

# Scaffold a new assistant visual-identity pack (Epic 3 Story 3.7).
# Usage: make new-visual-pack NAME=dog DISPLAY_NAME="Dog" CATEGORY=animal
new-visual-pack:
	uv run --project services/kinward python scripts/new_visual_pack.py "$(NAME)" \
		--display-name "$(DISPLAY_NAME)" --category "$(CATEGORY)"

down:
	docker compose down

up:
	docker compose up --build
