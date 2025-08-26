# PIS Service Makefile
# Automates common development tasks

.PHONY: help install seed run test test-system clean dev check-mongo

# Default target
help:
	@echo "PIS Service - Available commands:"
	@echo "  make install      - Install Python dependencies"
	@echo "  make seed         - Seed database with Best Buy data"
	@echo "  make run          - Start the FastAPI server"
	@echo "  make test         - Run system tests"
	@echo "  make test-system  - Run comprehensive system tests"
	@echo "  make dev          - Start server and run tests on file changes"
	@echo "  make clean        - Clean cache files"
	@echo "  make check-mongo  - Check if MongoDB is running"

# Install dependencies
install:
	pip install -r requirements.txt

# Check if MongoDB is running
check-mongo:
	@echo "Checking MongoDB connection..."
	@python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017'); client.server_info(); print('✓ MongoDB is running')" || (echo "✗ MongoDB is not running. Please start it with: brew services start mongodb-community" && exit 1)

# Seed database with real Best Buy data  
seed: check-mongo
	@echo "Seeding database with REAL Best Buy product data..."
	@echo "NOTE: This fetches real products from Best Buy API"
	python seed_bestbuy_data.py

# Run the FastAPI server
run:
	uvicorn app.main:app --reload --port 8000

# Run the FastAPI server in background
run-background:
	@echo "Starting server in background..."
	@uvicorn app.main:app --reload --port 8000 > server.log 2>&1 &
	@sleep 3
	@echo "Server started. PID saved to server.pid"
	@ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $$2}' > server.pid

# Stop background server
stop:
	@if [ -f server.pid ]; then \
		kill `cat server.pid` 2>/dev/null || true; \
		rm -f server.pid; \
		echo "Server stopped"; \
	else \
		echo "No server.pid file found"; \
	fi

# Run system tests
test: test-system

# Run comprehensive system tests
test-system:
	@echo "Running system tests..."
	@python test_system.py

# Run tests with server auto-start
test-with-server: run-background
	@echo "Waiting for server to start..."
	@sleep 2
	@python test_system.py || true
	@make stop

# Development mode - run server and watch for changes
dev:
	@echo "Starting development mode..."
	@echo "Server will reload on file changes"
	@echo "Press Ctrl+C to stop"
	uvicorn app.main:app --reload --port 8000

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -f server.pid server.log
	rm -f cookies.txt
	@echo "Cache files cleaned"

# Run tests on file change (requires watchdog)
watch-test:
	@echo "Watching for file changes..."
	@which watchmedo > /dev/null || (echo "Installing watchdog..." && pip install watchdog)
	watchmedo shell-command \
		--patterns="*.py" \
		--recursive \
		--command='clear && echo "Running tests..." && python test_system.py' \
		.

# Full test suite with coverage (requires pytest and coverage)
test-full:
	@which pytest > /dev/null || pip install pytest pytest-asyncio pytest-cov
	pytest tests/ --cov=app --cov-report=term-missing

# Lint code (requires flake8)
lint:
	@which flake8 > /dev/null || pip install flake8
	flake8 app/ --max-line-length=120 --exclude=__pycache__

# Format code (requires black)
format:
	@which black > /dev/null || pip install black
	black app/ --line-length=120

# Type check (requires mypy)
typecheck:
	@which mypy > /dev/null || pip install mypy
	mypy app/ --ignore-missing-imports

# Run all checks before commit
pre-commit: lint typecheck test-system
	@echo "✓ All checks passed"

# Docker commands
docker-build:
	docker build -t pis-service .

docker-run:
	docker run -p 8000:8000 --env-file .env pis-service

# Database management
db-backup:
	@echo "Backing up database..."
	@mkdir -p backups
	@mongodump --db=pis_service --out=backups/backup_$$(date +%Y%m%d_%H%M%S)
	@echo "Backup completed"

db-restore:
	@echo "Available backups:"
	@ls -la backups/
	@echo "To restore, run: mongorestore --db=pis_service backups/backup_TIMESTAMP/pis_service"

# Quick commands for development
q-test: test-system  # Quick test alias
q-run: run           # Quick run alias
q-seed: seed         # Quick seed alias