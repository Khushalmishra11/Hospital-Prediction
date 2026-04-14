#!/bin/bash

echo "Hospital Prediction System - Quick Start"
echo "========================================="
echo ""

# Check if running from the correct directory
if [ ! -d "backend" ]; then
    echo "Error: Please run this script from the Hospital-Prediction root directory"
    exit 1
fi

# Start Backend
echo "Starting Backend..."
cd backend/app
echo "Backend will start on http://localhost:8000"
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 2

# Start Frontend
echo ""
echo "Starting Frontend..."
cd ../../frontend
echo "Frontend will start on http://localhost:5173"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "================================================"
echo "Both servers are starting!"
echo ""
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "If you see errors:"
echo "1. Make sure you've installed dependencies:"
echo "   - Backend: pip install -r requirements.txt"
echo "   - Frontend: npm install"
echo "2. Check that .env files are properly configured"
echo "================================================"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
