# UATP Capsule Engine - Development Makefile
# ============================================
# Run `make help` to see available commands

.PHONY: help install dev test lint format security clean docker-build docker-up docker-down frontend-dev frontend-build

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)UATP Capsule Engine$(NC) - Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# =============================================================================
# INSTALLATION
# =============================================================================

install: ## Install all dependencies
	pip install -r requirements.txt
	pip install -e ".[test,dev]"
	cd frontend && npm install

install-dev: ## Install development dependencies only
	pip install -e ".[test,dev]"
	pre-commit install

# =============================================================================
# DEVELOPMENT
# =============================================================================

dev: ## Start development server (backend)
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

frontend-dev: ## Start frontend development server
	cd frontend && npm run dev

dev-all: ## Start both backend and frontend (requires tmux or run in separate terminals)
	@echo "$(YELLOW)Run these in separate terminals:$(NC)"
	@echo "  make dev          # Backend on :8000"
	@echo "  make frontend-dev # Frontend on :3000"

# =============================================================================
# TESTING
# =============================================================================

test: ## Run all tests
	pytest tests/ -v --ignore=tests/legacy --ignore=tests/integration

test-unit: ## Run unit tests only
	pytest tests/ -v --ignore=tests/legacy --ignore=tests/integration --ignore=tests/capture

test-integration: ## Run integration tests
	pytest tests/integration/ -v

test-cov: ## Run tests with coverage report
	pytest tests/ -v --ignore=tests/legacy --cov=src --cov-report=term-missing --cov-report=html

test-watch: ## Run tests in watch mode
	ptw tests/ -- -v --ignore=tests/legacy

# =============================================================================
# CODE QUALITY
# =============================================================================

lint: ## Run all linters
	ruff check src/ tests/ --exclude tests/legacy
	mypy src/ --ignore-missing-imports

format: ## Format code
	ruff format src/ tests/ --exclude tests/legacy
	ruff check src/ tests/ --exclude tests/legacy --fix

format-check: ## Check code formatting without changes
	ruff format --check src/ tests/ --exclude tests/legacy

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

# =============================================================================
# SECURITY
# =============================================================================

security: ## Run security checks
	bandit -r src/ -f json -o bandit-report.json || true
	@echo "$(GREEN)Security scan complete. Check bandit-report.json$(NC)"

security-deps: ## Check dependencies for vulnerabilities
	safety scan || true

gitleaks: ## Scan for secrets in git history
	gitleaks detect --source . -v

# =============================================================================
# DATABASE
# =============================================================================

db-migrate: ## Run database migrations
	alembic upgrade head

db-rollback: ## Rollback last migration
	alembic downgrade -1

db-reset: ## Reset database (WARNING: destroys data)
	@echo "$(RED)WARNING: This will destroy all data!$(NC)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
	rm -f uatp_dev.db
	alembic upgrade head

# =============================================================================
# DOCKER
# =============================================================================

docker-build: ## Build Docker image
	docker build -t uatp-capsule-engine:dev .

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker container logs
	docker-compose logs -f

docker-prod: ## Build and run production Docker setup
	docker-compose -f docker-compose.prod.yml up --build

# =============================================================================
# FRONTEND
# =============================================================================

frontend-build: ## Build frontend for production
	cd frontend && npm run build

frontend-lint: ## Lint frontend code
	cd frontend && npm run lint

frontend-test: ## Run frontend tests
	cd frontend && npm test

# =============================================================================
# CLEANUP
# =============================================================================

clean: ## Clean build artifacts and caches
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov/ .coverage coverage.xml
	rm -rf dist/ build/ *.egg-info
	rm -rf bandit-report.json safety-report.json
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-all: clean ## Clean everything including node_modules
	rm -rf frontend/node_modules frontend/.next

# =============================================================================
# RELEASE
# =============================================================================

version: ## Show current version
	@python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"

changelog: ## Generate changelog (requires git-cliff)
	git-cliff -o CHANGELOG.md
