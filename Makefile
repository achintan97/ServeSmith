.PHONY: dev test lint run

dev:
	pip install -e ".[dev]"

run:
	uvicorn servesmith.server:app --reload --port 8000

test:
	pytest -v

lint:
	ruff check src/ tests/
