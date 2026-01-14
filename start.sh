#!/bin/bash

# KOMAS v4.0 - Startup Script
# ===========================
# This script starts both backend and frontend servers

echo "🚀 Starting KOMAS v4.0..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}⚠️  Backend already running on port 8000${NC}"
else
    echo -e "${BLUE}📡 Starting Backend (port 8000)...${NC}"
    cd backend
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /dev/null 2>&1 &
    BACKEND_PID=$!
    cd ..
    echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
fi

# Wait a moment for backend to initialize
sleep 2

# Check if frontend is already running
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}⚠️  Frontend already running on port 5173${NC}"
else
    echo -e "${BLUE}🎨 Starting Frontend (port 5173)...${NC}"
    cd frontend
    npm run dev > /dev/null 2>&1 &
    FRONTEND_PID=$!
    cd ..
    echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 KOMAS v4.0 is ready!${NC}"
echo ""
echo "📊 Access Points:"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "⚠️  PAPER TRADING ONLY - No real trading occurs"
echo ""
echo "To stop servers:"
echo "  pkill -f uvicorn"
echo "  pkill -f vite"
