#!/usr/bin/env bash

# Script to start both frontend and backend
# Usage: ./run.sh

# Start backend
echo "Starting Flask Backend on port 5000..."
cd backend
python -m venv venv
source venv/bin/activate || source venv/Scripts/activate
pip install -r requirements.txt
python app.py &
BACKEND_PID=$!
cd ..

# Start frontend
echo "Starting React Frontend..."
cd honeypot-collegeportal
npm install
npm run dev &
FRONTEND_PID=$!
cd ..

echo "Both services started. Press Ctrl+C to stop."

trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait
