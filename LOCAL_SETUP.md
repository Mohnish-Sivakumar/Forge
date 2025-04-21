# Local Setup Guide

This guide explains how to run the Voice Assistant application locally with your Speechify API key.

## Option 1: Using the run script (Recommended)

The easiest way to run the application is to use the provided script:

```bash
./run_with_api.sh
```

This script:
1. Sets up all necessary environment variables including your Speechify API key
2. Starts both the backend and frontend servers
3. Configures proper logging

## Option 2: Manual Setup

If you prefer to run the servers manually:

### Backend Setup

```bash
# Set environment variables
export SPEECHIFY_API_KEY="fwsjj7SjBEmJ9C058GN5NLEEIfwOga3tYKkftbo_TQE="
export FLASK_APP=backend/app.py
export FLASK_ENV=development

# Start the backend server
cd backend
python -m flask run --port=5001
```

### Frontend Setup

Open a new terminal window and run:

```bash
# Navigate to frontend directory
cd my-voice-assistant

# Start the React development server
npm start
```

## API Key Information

The Speechify API key (fwsjj7SjBEmJ9C058GN5NLEEIfwOga3tYKkftbo_TQE=) has been configured in:

1. Environment variables through the run scripts
2. Directly in the `api/index.py` file as a fallback default

## Troubleshooting

If you encounter issues:

1. Make sure both servers are running (backend on port 5001, frontend on port 3000)
2. Check the console logs for any error messages
3. Verify that your API key is correctly set
4. Try accessing the API directly with: http://localhost:5001/api/debug 