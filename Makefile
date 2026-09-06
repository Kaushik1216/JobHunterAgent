.PHONY: install lint format typecheck test evaluate run dashboard docker-up docker-down clean

install:
	uv pip install -e ".[dev]"

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy src tests

test:
	pytest

evaluate:
	@echo "Evaluating..."

run:
	job-agent

dashboard:
	streamlit run src/job_agent/dashboard/app.py

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
