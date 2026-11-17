.PHONY: api-test api-lint
api-test:
	cd services/api && uv run pytest -q
api-lint:
	cd services/api && uv run ruff check . && uv run mypy app
