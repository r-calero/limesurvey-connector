SOURCES ?= local

.PHONY: sync lint format typecheck test conformance goldens goldens-check build audit

sync:
	uv sync --all-extras --all-packages

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	uv run mypy

test:
	uv run pytest -m "not integration"

conformance:
	uv run pytest -m conformance

goldens:
	uv run python conformance/generate/run.py --sources $(SOURCES)

goldens-check:
	uv run python conformance/generate/run.py --sources $(SOURCES) --check

build:
	uv build --all-packages

audit:
	uv run pip-audit
