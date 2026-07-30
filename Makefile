SHELL := /bin/bash

.PHONY: up down logs test lint format migrate seed clean

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

test:
	docker compose run --rm backend pytest -q
	docker compose run --rm frontend-tooling npm run test -- --run

lint:
	docker compose run --rm backend ruff check app tests
	docker compose run --rm frontend-tooling npm run lint

format:
	docker compose run --rm backend ruff format app tests

migrate:
	docker compose run --rm backend alembic upgrade head

seed:
	docker compose run --rm backend python -m app.database.bootstrap

clean:
	docker compose down -v --remove-orphans
