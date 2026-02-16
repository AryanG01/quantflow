.PHONY: install lint test test-unit test-integration format typecheck db-up db-down

install:
	uv sync --all-extras

lint: format typecheck
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	uv run mypy packages/ apps/ scripts/

test:
	uv run pytest tests/

test-unit:
	uv run pytest tests/unit/

test-integration:
	uv run pytest tests/integration/ -m integration

db-up:
	docker compose -f docker-compose.dev.yml up -d

db-down:
	docker compose -f docker-compose.dev.yml down

backfill:
	uv run python scripts/backfill_candles.py

backtest:
	uv run python scripts/run_backtest.py
