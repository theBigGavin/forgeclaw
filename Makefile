# ForgeClaw Makefile

.PHONY: help install test test-bootstrap test-api start start-web clean

help:
	@echo "ForgeClaw - 确定性 AI Agent 编排平台"
	@echo ""
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make test          - Run all tests"
	@echo "  make test-bootstrap- Run bootstrap tests (self-check)"
	@echo "  make test-api      - Run API integration tests"
	@echo "  make start         - Start API server"
	@echo "  make start-web     - Start both API and Web UI"
	@echo "  make clean         - Clean up processes"
	@echo "  make verify        - Verify installation and configuration"

install:
	@echo "📦 Installing Python dependencies..."
	pip install -e ".[dev]"
	@echo "📦 Installing Node dependencies..."
	cd web && npm install

test: test-bootstrap test-api
	@echo "✅ All tests completed"

test-bootstrap:
	@echo "🔬 Running bootstrap tests..."
	@python3 tests/test_bootstrap.py

test-api:
	@echo "🧪 Running API integration tests..."
	@python3 tests/verify_endpoints.py

verify:
	@echo "🔍 Verifying installation..."
	@echo ""
	@echo "Checking Python packages:"
	@python3 -c "import fastapi; print('  ✓ FastAPI')" 2>/dev/null || echo "  ✗ FastAPI missing"
	@python3 -c "import uvicorn; print('  ✓ Uvicorn')" 2>/dev/null || echo "  ✗ Uvicorn missing"
	@python3 -c "import httpx; print('  ✓ HTTPX')" 2>/dev/null || echo "  ✗ HTTPX missing"
	@echo ""
	@echo "Checking Node packages:"
	@cd web && npm list react 2>/dev/null | grep -q react && echo "  ✓ React" || echo "  ✗ React missing"
	@echo ""
	@echo "Checking configuration:"
	@if [ -f ".env" ]; then echo "  ✓ .env file exists"; else echo "  ✗ .env file missing (copy .env.example)"; fi
	@if grep -q "OPENAI_API_KEY=" .env 2>/dev/null; then echo "  ✓ API key configured"; else echo "  ✗ API key not configured"; fi

start:
	@./start.sh

start-web:
	@./start.sh --web

clean:
	@echo "🧹 Cleaning up..."
	@pkill -f "uvicorn" 2>/dev/null || true
	@pkill -f "vite" 2>/dev/null || true
	@echo "✅ Processes stopped"
