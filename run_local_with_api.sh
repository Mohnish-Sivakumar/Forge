#!/bin/bash

# Set environment variables
export DEEPGRAM_API_KEY="76bcd98ea7b5eee683a740e132e60aac0fae266a"
export FLASK_APP=backend/app.py
export FLASK_ENV=development
export SERVE_STATIC=true

# Print starting information
echo "=== Starting Voice Assistant with API Keys ==="
echo "Deepgram API Key: ${DEEPGRAM_API_KEY:0:5}...${DEEPGRAM_API_KEY:(-5)}"
echo "Working directory: $(pwd)"

# Start the backend server
echo "Starting backend server on port 5001..."
cd backend && python -m flask run --port=5001 &
BACKEND_PID=$!

# Wait for backend to start
sleep 2
echo "Backend server started with PID: $BACKEND_PID"

# Start the frontend server
echo "Starting frontend..."
cd ../my-voice-assistant && npm start

# When the React app is terminated, also stop the Flask server
kill $BACKEND_PID 