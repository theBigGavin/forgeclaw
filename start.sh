#!/bin/bash

# ForgeClaw Launcher - Starts API server and optionally the web UI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
WEB_UI=false
API_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --web|-w)
            WEB_UI=true
            shift
            ;;
        --api-only|-a)
            API_ONLY=true
            shift
            ;;
        --help|-h)
            echo -e "${BLUE}ForgeClaw Launcher${NC}"
            echo ""
            echo "Usage: ./start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -w, --web      Start both API server and web UI"
            echo "  -a, --api-only Start only the API server (default)"
            echo "  -h, --help     Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./start.sh           # Start API server only"
            echo "  ./start.sh -w        # Start both API and web UI"
            echo "  ./start.sh --web     # Start both API and web UI"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}╔════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         ForgeClaw v0.1.0           ║${NC}"
echo -e "${BLUE}║   Deterministic Workflow Engine    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════╝${NC}"
echo ""

# Check if python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    exit 1
fi

# Activate virtual environment if exists
if [ -f ".venv/bin/activate" ]; then
    echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo -e "${YELLOW}📄 Loading environment from .env...${NC}"
    export $(grep -v '^#' .env | xargs)
fi

# Check required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  Warning: OPENAI_API_KEY not set. Planner functionality will not work.${NC}"
    echo -e "${YELLOW}   Copy .env.example to .env and add your API key.${NC}"
    echo ""
fi

# Check if Node.js is available (for web UI)
if [ "$WEB_UI" = true ]; then
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}Error: npm not found. Cannot start web UI.${NC}"
        exit 1
    fi
fi

# Start API Server
echo -e "${YELLOW}🚀 Starting API Server...${NC}"

# 确保 src 目录在 Python 路径中
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# 启动 uvicorn
python3 -m uvicorn forgeclaw.api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!
echo -e "${GREEN}✓ API Server started (PID: $API_PID)${NC}"
echo -e "${BLUE}  → API: http://localhost:8000${NC}"
echo -e "${BLUE}  → Docs: http://localhost:8000/docs${NC}"

# Wait a moment for API to start
sleep 2

# Start Web UI if requested
if [ "$WEB_UI" = true ]; then
    echo ""
    echo -e "${YELLOW}🎨 Starting Web UI...${NC}"
    cd web
    npm run dev &
    WEB_PID=$!
    echo -e "${GREEN}✓ Web UI started (PID: $WEB_PID)${NC}"
    echo -e "${BLUE}  → UI: http://localhost:5173${NC}"
    cd ..
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}  All services started successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Trap Ctrl+C to kill all processes
trap 'echo ""; echo -e "${YELLOW}🛑 Stopping services...${NC}"; kill $API_PID 2>/dev/null; kill $WEB_PID 2>/dev/null; exit 0' INT

# Wait for processes
wait
