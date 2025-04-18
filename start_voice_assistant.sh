#!/bin/bash

echo "==== Voice Assistant Setup & Launch ===="
echo "This script will download voice files and start the application."
echo

# Create voice files directory if it doesn't exist
mkdir -p api/voice_files

# Check Python availability
if ! command -v python &> /dev/null; then
    echo "Error: Python not found. Please install Python 3."
    exit 1
fi

# Download voice files
echo "Step 1: Downloading voice files..."
python check_voice_files.py

# Ensure environment variables are set
export FLASK_APP=backend/app.py
export FLASK_ENV=development
export GOOGLE_API_KEY=${GOOGLE_API_KEY:-"AIzaSyDrxMRoQ-Knm7gM_6YNHAiPhXoC6HN09S4"}

# Start the Flask backend in the background
echo "Step 2: Starting backend server on port 5001..."
cd backend && python -m flask run --port=5001 &
BACKEND_PID=$!

# Give the backend time to start
sleep 3
echo "Backend server started with PID: $BACKEND_PID"

# Start the React frontend in a new terminal window if possible
echo "Step 3: Starting frontend..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell app "Terminal" to do script "cd '$(pwd)'/my-voice-assistant && npm start"'
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux with graphical environment
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash -c "cd $(pwd)/my-voice-assistant && npm start; exec bash"
    elif command -v xterm &> /dev/null; then
        xterm -e "cd $(pwd)/my-voice-assistant && npm start" &
    else
        # Fall back to background process
        echo "Couldn't find a terminal emulator. Starting frontend in background..."
        cd $(pwd)/my-voice-assistant && npm start &
        FRONTEND_PID=$!
        echo "Frontend started with PID: $FRONTEND_PID"
    fi
else
    # Windows or other OS - just run in background
    cd my-voice-assistant && npm start &
    FRONTEND_PID=$!
    echo "Frontend started with PID: $FRONTEND_PID"
fi

echo
echo "=== Voice Assistant Started ==="
echo "Backend running at: http://localhost:5001"
echo "Frontend running at: http://localhost:3000"
echo
echo "Press Ctrl+C to stop backend server"
echo "(Close frontend window/tab manually or kill process)"

# Keep script running until Ctrl+C
wait $BACKEND_PID 