# Running the Voice Assistant Application

This document explains the different ways to run the Voice Assistant application locally.

## Option 1: Using the CommonJS Script (Recommended)

```bash
./run_with_api.sh
```

This script:
1. Sets the necessary environment variables (Speechify API key and Gemini API key)
2. Runs the `dev.cjs` script using Node.js
3. The script starts both the backend and frontend in a single terminal with nice logging

## Option 2: Manual Start Script

If the above method doesn't work, try:

```bash
./start-manually.sh
```

This script:
1. Sets the necessary environment variables
2. Starts the Flask backend in the current terminal
3. Opens a new terminal window to run the frontend (on macOS) or runs it in the background (on Linux)
4. Does not rely on Node.js to manage the processes

## Option 3: Run Components Separately

If you prefer to run each component manually:

### Backend

```bash
# Set environment variables
export SPEECHIFY_API_KEY="fwsjj7SjBEmJ9C058GN5NLEEIfwOga3tYKkftbo_TQE="
export GEMINI_API_KEY="AIzaSyDrxMRoQ-Knm7gM_6YNHAiPhXoC6HN09S4"
export FLASK_APP=backend/app.py
export FLASK_ENV=development

# Run backend
cd backend
python -m flask run --port=5001
```

### Frontend

In a separate terminal:

```bash
cd my-voice-assistant
npm start
```

## Troubleshooting

If you encounter issues:

1. **Module Error**: If you see an error about ES modules vs CommonJS, it means there's a mismatch between how Node.js is handling your JavaScript files. Try using the `.cjs` file or the manual script method.

2. **Port Already in Use**: If you see an error that a port is already in use, try running:
   ```bash
   # For port 5001 (backend)
   lsof -ti:5001 | xargs kill -9
   
   # For port 3000 (frontend)
   lsof -ti:3000 | xargs kill -9
   ```

3. **Check API Key**: Verify the Speechify API key is correct:
   ```bash
   # Testing Speechify API
   curl -X POST \
     -H "Authorization: Bearer fwsjj7SjBEmJ9C058GN5NLEEIfwOga3tYKkftbo_TQE=" \
     -H "Content-Type: application/json" \
     -d '{"input":"Hello world", "voice_id":"belinda"}' \
     https://api.sws.speechify.com/v1/audio/speech
   ```

For more detailed information, refer to the `LOCAL_SETUP.md` file. 