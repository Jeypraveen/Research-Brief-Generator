# Research Brief Generator Makefile

.PHONY: help install setup test run-cli run-web run-api clean lint format check health

# Default target
help:
	@echo "Research Brief Generator - Available Commands:"
	@echo ""
	@echo "Setup and Installation:"
	@echo "  make install    - Install all dependencies"
	@echo "  make setup      - Setup the environment and configuration"
	@echo ""
	@echo "Running the Application:"
	@echo "  make run-cli    - Run CLI interface with example"
	@echo "  make run-web    - Start Flask web application"
	@echo "  make run-api    - Start FastAPI server"
	@echo ""
	@echo "Development and Testing:"
	@echo "  make test       - Run all tests"
	@echo "  make lint       - Run linting checks"
	@echo "  make format     - Format code with black"
	@echo "  make check      - Run all checks (lint + test)"
	@echo ""
	@echo "Utilities:"
	@echo "  make health     - Run health check"
	@echo "  make clean      - Clean up temporary files"
	@echo "  make docs       - Generate documentation"

install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt

setup:
	@echo "⚙️ Setting up environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file. Please edit it with your API keys."; fi
	@python -c "from src.config import config; print('✅ Configuration validated!' if config.validate_config() else '❌ Please set your GEMINI_API_KEY in .env')"

run-cli:
	@echo "🚀 Running CLI with example query..."
	python main.py --topic "Artificial Intelligence in Healthcare" --depth 3 --verbose

run-web:
	@echo "🌐 Starting Flask web application..."
	python main.py --web-app --port 5000

run-api:
	@echo "⚡ Starting FastAPI server..."
	python main.py --api --port 8000

test:
	@echo "🧪 Running tests..."
	python -m pytest tests/ -v

lint:
	@echo "🔍 Running linting checks..."
	@command -v flake8 >/dev/null 2>&1 || { echo "Installing flake8..."; pip install flake8; }
	flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503

format:
	@echo "✨ Formatting code..."
	@command -v black >/dev/null 2>&1 || { echo "Installing black..."; pip install black; }
	black src/ tests/ --line-length=100

check: lint test
	@echo "✅ All checks passed!"

health:
	@echo "🏥 Running health check..."
	python main.py --health-check

clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/

docs:
	@echo "📚 Generating documentation..."
	@command -v mkdocs >/dev/null 2>&1 || { echo "Installing mkdocs..."; pip install mkdocs mkdocs-material; }
	@if [ ! -f mkdocs.yml ]; then echo "mkdocs.yml not found. Run 'mkdocs new .' first."; exit 1; fi
	mkdocs build

dev-install:
	@echo "🔧 Installing development dependencies..."
	pip install -e .
	pip install black flake8 pytest pytest-asyncio mkdocs mkdocs-material

docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t research-brief-generator .

docker-run:
	@echo "🐳 Running Docker container..."
	docker run -p 8000:8000 --env-file .env research-brief-generator

# Quick deployment
deploy-heroku:
	@echo "🚀 Deploying to Heroku..."
	@if [ ! -f Procfile ]; then echo "web: python main.py --api --host 0.0.0.0 --port \\$$PORT" > Procfile; fi
	git add . && git commit -m "Deploy to Heroku" && git push heroku main

# Virtual environment setup
venv:
	@echo "🐍 Creating virtual environment..."
	python -m venv venv
	@echo "Activate with: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)"

requirements-update:
	@echo "📋 Updating requirements.txt..."
	pip freeze > requirements.txt	