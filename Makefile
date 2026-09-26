.PHONY: install lint format typecheck test evaluate run dashboard dev clean

install:
	uv pip install -e ".[dev]"

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy src tests

test:
	uv run pytest tests/ -v

evaluate:
	@echo "Evaluating..."

run:
	uv run job-agent

dashboard:
	cd frontend && npm install && npm run build
	uv run job-agent dashboard

dev:
	cd frontend && npm install && npm run build && cd .. && uv run job-agent dashboard

clean:
	Remove-Item -Recurse -Force -ErrorAction SilentlyContinue .pytest_cache, .ruff_cache, .mypy_cache, build, dist
	Get-ChildItem -Recurse -Directory -Name __pycache__ | Remove-Item -Recurse -Force
