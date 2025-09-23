.PHONY: setup lint fmt test run clean help

# Default target
help:
	@echo "Available targets:"
	@echo "  setup  - Create venv, install deps + dev extras, install pre-commit hooks"
	@echo "  lint   - Run ruff + black check"
	@echo "  fmt    - Format code with black"
	@echo "  test   - Run pytest with coverage"
	@echo "  run    - Start FastAPI app (if exists)"
	@echo "  clean  - Clean up generated files"
	@echo "  help   - Show this help message"

setup:
	@echo "🚀 Setting up Okra development environment..."
	python -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/pip install -e .[dev]
	.venv/bin/pip install pytest-cov
	.venv/bin/pip install pre-commit
	.venv/bin/pre-commit install
	@echo "✅ Setup complete! Activate with: source .venv/bin/activate"

lint:
	@echo "🔍 Running linting checks..."
	.venv/bin/ruff check .
	.venv/bin/black --check .
	@echo "✅ Linting passed!"

fmt:
	@echo "🎨 Formatting code..."
	.venv/bin/black .
	.venv/bin/ruff format .
	@echo "✅ Code formatted!"

test:
	@echo "🧪 Running tests with coverage..."
	.venv/bin/pytest -q --cov=src --cov-report=term-missing --cov-fail-under=80
	@echo "✅ Tests passed!"

run:
	@echo "🚀 Starting Okra service..."
	@if [ -f "src/okra/api.py" ]; then \
		.venv/bin/uvicorn okra.api:app --reload --port 8000; \
	else \
		echo "❌ FastAPI app not found at src/okra/api.py"; \
		exit 1; \
	fi

clean:
	@echo "🧹 Cleaning up..."
	rm -rf .venv
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete!"
