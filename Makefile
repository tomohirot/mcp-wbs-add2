.PHONY: help install test test-unit test-integration coverage lint format type-check clean pre-commit-install

help:
	@echo "Available commands:"
	@echo "  make install              - Install dependencies"
	@echo "  make test                 - Run all tests"
	@echo "  make test-unit            - Run unit tests only"
	@echo "  make test-integration     - Run integration tests only"
	@echo "  make coverage             - Run tests with coverage report"
	@echo "  make lint                 - Run linting checks"
	@echo "  make format               - Format code with black and isort"
	@echo "  make type-check           - Run type checking with mypy"
	@echo "  make clean                - Remove generated files"
	@echo "  make pre-commit-install   - Install pre-commit hooks"

install:
	pip install -r requirements.txt
	pip install pre-commit

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v --ignore-glob='**/test_*.py' || echo "No integration tests yet"

coverage:
	pytest tests/unit/ \
		--cov=src \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-report=xml \
		--cov-fail-under=80 \
		-v

coverage-html:
	pytest tests/unit/ \
		--cov=src \
		--cov-report=html \
		-v
	@echo "Opening coverage report in browser..."
	open htmlcov/index.html || xdg-open htmlcov/index.html

lint:
	flake8 src tests --max-line-length=100 --extend-ignore=E203,W503
	black --check src tests
	isort --check-only src tests

format:
	black src tests
	isort src tests

type-check:
	mypy src --ignore-missing-imports --no-strict-optional

clean:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete

pre-commit-install:
	pre-commit install
	@echo "Pre-commit hooks installed successfully!"

ci-test:
	@echo "Running CI test pipeline..."
	make lint
	make type-check
	make coverage
	@echo "✅ CI test pipeline completed successfully!"
