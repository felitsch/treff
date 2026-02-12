#!/bin/bash
set -e

echo "============================================"
echo "  TREFF Sprachreisen Post-Generator"
echo "  Development Environment Setup"
echo "============================================"
echo ""

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    PIP_CMD="pip"
else
    echo -e "${RED}Error: Python 3.11+ is required but not found.${NC}"
    echo "Please install Python: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python: $PYTHON_VERSION${NC}"

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js: $NODE_VERSION${NC}"
else
    echo -e "${RED}Error: Node.js 18+ is required but not found.${NC}"
    echo "Please install Node.js: https://nodejs.org/"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓ npm: $NPM_VERSION${NC}"
else
    echo -e "${RED}Error: npm is required but not found.${NC}"
    exit 1
fi

echo ""

# ===== BACKEND SETUP =====
echo -e "${YELLOW}Setting up backend...${NC}"
cd "$PROJECT_DIR/backend"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# Create .env if it doesn't exist
if [ ! -f "$PROJECT_DIR/backend/.env" ]; then
    cp "$PROJECT_DIR/backend/.env.example" "$PROJECT_DIR/backend/.env" 2>/dev/null || true
    echo -e "${YELLOW}Note: Create backend/.env with your API keys for full functionality${NC}"
fi

cd "$PROJECT_DIR"

# ===== FRONTEND SETUP =====
echo -e "${YELLOW}Setting up frontend...${NC}"
cd "$PROJECT_DIR/frontend"

# Install Node dependencies
echo "Installing Node.js dependencies..."
npm install --silent 2>/dev/null || npm install

echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

cd "$PROJECT_DIR"

echo ""
echo "============================================"
echo -e "${YELLOW}Starting development servers...${NC}"
echo "============================================"
echo ""

# Kill any existing servers on our ports
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
lsof -ti :5173 | xargs kill -9 2>/dev/null || true
sleep 1

# Start backend
echo "Starting FastAPI backend on port 8000..."
cd "$PROJECT_DIR/backend"
source venv/bin/activate
$PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd "$PROJECT_DIR"

# Start frontend
echo "Starting Vite dev server on port 5173..."
cd "$PROJECT_DIR/frontend"
npm run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!
cd "$PROJECT_DIR"

# Wait for servers to start
echo ""
echo "Waiting for servers to start..."
sleep 5

echo ""
echo "============================================"
echo -e "${GREEN}  Development servers running!${NC}"
echo "============================================"
echo ""
echo -e "  Frontend:  ${GREEN}http://localhost:5173${NC}"
echo -e "  Backend:   ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs:  ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  Health:    ${GREEN}http://localhost:8000/api/health${NC}"
echo ""
echo "  Press Ctrl+C to stop all servers"
echo ""

# Wait for either process
wait $BACKEND_PID $FRONTEND_PID
