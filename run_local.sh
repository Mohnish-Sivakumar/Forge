#!/bin/bash

# Export required environment variables
export FLASK_APP=backend/app.py
export FLASK_ENV=development

# Start Flask backend in the background
echo "Starting Flask backend server on port 5001..."
flask run --port=5001 &
FLASK_PID=$!

# Start the React frontend
echo "Starting React frontend..."
cd my-voice-assistant && npm start

# When the React app is stopped, also stop the Flask server
kill $FLASK_PID 