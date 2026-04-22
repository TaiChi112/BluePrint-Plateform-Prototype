#!/bin/bash
# Quick Start Script for Calendar Agent System
# Usage: bash quickstart.sh [mode]

set -e

MODE=${1:-"mock"}  # Default to mock mode
PURPLE='\033[0;35m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${PURPLE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║   📅 Calendar Agent - Quick Start Script       ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Check dependencies
echo -e "${YELLOW}Step 1: Checking dependencies...${NC}"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo "❌ pip not found. Please install pip"
    exit 1
fi

echo -e "${GREEN}✅ Python found: $(python3 --version)${NC}"
echo ""

# Step 2: Create virtual environment
echo -e "${YELLOW}Step 2: Setting up virtual environment...${NC}"

if [ ! -d "venv" ]; then
    echo "Creating venv..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate venv
source venv/bin/activate || . venv/Scripts/activate

echo ""

# Step 3: Install dependencies
echo -e "${YELLOW}Step 3: Installing dependencies...${NC}"

pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 4: Setup environment file
echo -e "${YELLOW}Step 4: Setting up environment...${NC}"

if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "CALENDAR_MODE=$MODE" >> .env
    echo -e "${GREEN}✅ .env file created with MODE=$MODE${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

echo ""

# Step 5: Run tests
echo -e "${YELLOW}Step 5: Running tests...${NC}"

python3 -m pytest test_main.py -q --tb=short 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Some tests might have failed (OK for now)${NC}"
}

echo ""

# Step 6: Show next steps
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Ready to Run Calendar Agent!           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}Choose how to run:${NC}"
echo ""
echo "📖 Option 1: Web UI (Flask)"
echo "   ${GREEN}python app.py${NC}"
echo "   Then open: http://localhost:5000"
echo ""

echo "🖥️  Option 2: Command Line (Interactive)"
echo "   ${GREEN}python main.py${NC}"
echo "   Follow the prompts to create events"
echo ""

echo "📅 Option 3: Example Usage"
echo "   ${GREEN}python example_usage.py --interactive${NC}"
echo ""

echo "🧪 Option 4: Run Tests"
echo "   ${GREEN}python -m pytest test_main.py -v${NC}"
echo ""

if [ "$MODE" = "api" ]; then
    echo -e "${YELLOW}⚠️  You selected API mode.${NC}"
    echo "Make sure credentials.json is in this folder!"
    echo ""
fi

if [ "$MODE" = "mcp" ]; then
    echo -e "${YELLOW}⚠️  You selected MCP mode.${NC}"
    echo "Make sure MCP server is running:"
    echo "   ${GREEN}cd mcp-server && npm install && node server.js${NC}"
    echo ""
fi

echo -e "${YELLOW}Docker users:${NC}"
echo "   ${GREEN}docker-compose up --build${NC}"
echo ""

echo -e "${GREEN}Happy scheduling! 📅${NC}"
