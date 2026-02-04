.PHONY: help install dev test test-unit test-int test-e2e test-cov lint lint-fix type-check format docker-up docker-down docker-logs clean vendor-setup playwright-install

help:
	@echo "Available targets:"
	@echo "  install             Install production dependencies"
	@echo "  dev                 Install dev dependencies and setup pre-commit"
	@echo "  test                Run all tests"
	@echo "  test-unit           Run unit tests only"
	@echo "  test-int            Run integration tests"
	@echo "  test-e2e            Run e2e tests"
	@echo "  test-cov            Run tests with coverage"
	@echo "  lint                Run linting (ruff + mypy)"
	@echo "  lint-fix            Fix linting issues (ruff)"
	@echo "  type-check          Run mypy type checks"
	@echo "  format              Format code with ruff"
	@echo "  docker-up           Start infrastructure services"
	@echo "  docker-down         Stop infrastructure services"
	@echo "  docker-logs         Show docker logs"
	@echo "  clean               Clean build artifacts"
	@echo "  vendor-setup        Clone and setup vendor projects"
	@echo "  playwright-install  Install Playwright browsers"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"
	pre-commit install
	pre-commit install --hook-type commit-msg

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-int:
	pytest tests/integration/ -v

test-e2e:
	pytest tests/e2e/ -v -m e2e

test-cov:
	pytest tests/ --cov=src/aria --cov-report=html --cov-report=term

lint:
	ruff check src/ tests/
	mypy src/

lint-fix:
	ruff check --fix src/ tests/
	ruff format src/ tests/

type-check:
	mypy src/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

clean:
	python -c "import shutil, pathlib; paths=['.pytest_cache','.mypy_cache','.ruff_cache','build','dist']; [shutil.rmtree(p, ignore_errors=True) for p in paths]; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]"

vendor-setup:
	bash scripts/vendor-clone.sh

playwright-install:
	playwright install
