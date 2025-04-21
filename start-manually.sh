#!/bin/bash

# Set environment variables for API keys
export SPEECHIFY_API_KEY="fwsjj7SjBEmJ9C058GN5NLEEIfwOga3tYKkftbo_TQE="
export GEMINI_API_KEY="AIzaSyDrxMRoQ-Knm7gM_6YNHAiPhXoC6HN09S4"
export FLASK_APP=backend/app.py
export FLASK_ENV=development
export PYTHONUNBUFFERED=1

# Print API key information
echo "=== Starting Voice Assistant with API Keys ==="
echo "Speechify API Key: ${SPEECHIFY_API_KEY:0:5}...${SPEECHIFY_API_KEY:(-5)}"
echo "Gemini API Key: ${GEMINI_API_KEY:0:5}...${GEMINI_API_KEY:(-5)}"

# Detect OS for determining command approach
platform=$(uname)

# Stop any running servers on these ports
echo "Ensuring ports are available..."
if [[ "$platform" == "Darwin" ]]; then
    # macOS
    lsof -ti:5001 | xargs kill -9 2>/dev/null || true
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
elif [[ "$platform" == "Linux" ]]; then
    # Linux
    kill $(lsof -t -i:5001) 2>/dev/null || true
    kill $(lsof -t -i:3000) 2>/dev/null || true
fi

# Start the Flask backend in the background
echo "Starting backend server on port 5001..."
cd backend && python -m flask run --port=5001 &
BACKEND_PID=$!

# Wait for backend to start
sleep 2
echo "Backend server started with PID: $BACKEND_PID"

# Start the frontend in the most appropriate way based on OS
echo "Starting frontend on port 3000..."
cd ../my-voice-assistant

if [[ "$platform" == "Darwin" ]]; then
    # macOS: Open a new terminal window
    osascript -e 'tell app "Terminal" to do script "cd \"'"$(pwd)"'\" && npm start"'
    echo "Frontend started in a new terminal window"
else
    # Linux/Other: Just run in background and log to file
    npm start > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "Frontend started with PID: $FRONTEND_PID (logs in frontend.log)"
fi

# Keep script running until Ctrl+C
echo ""
echo "Voice Assistant is starting..."
echo "- Backend: http://localhost:5001"
echo "- Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the backend server"
echo "The frontend may need to be closed separately"

# Wait for user to press Ctrl+C
wait $BACKEND_PID 