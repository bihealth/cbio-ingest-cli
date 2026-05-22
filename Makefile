.PHONY: install
install:
	uv sync

.PHONY: format
format:
	uv run ruff format .

.PHONY: check
check:
	uv run ruff check .
	uv run ruff format --check .

.PHONY: type
type:
	uv run pyrefly check

.PHONY: fix
fix:
	uv run ruff check . --fix

.PHONY: test
test:
	uv run pytest --cov=cbio_ingest --cov-report=html --cov-report=term-missing
