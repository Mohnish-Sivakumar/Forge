# Development Setup Guide

Follow these steps to get your development environment working correctly. This will fix the "Cannot POST /api/voice" and 404 errors.

## Quick Start (Easiest Option)

Run both the backend and frontend at once:

```bash
npm run dev
```

This will start both servers in the correct configuration with proper logging.

## Manual Steps (If Quick Start Doesn't Work)

### 1. Start the Backend Server First

Open a terminal and run:

```bash
npm run backend
```

This starts the Flask backend on port 5001.

### 2. Start the Frontend Server

Open another terminal and run:

```bash
npm run frontend
```

This starts the React frontend on port 3000.

## Troubleshooting

If you're still getting 404 errors:

1. Make sure both servers are running (check terminal output)
2. Check that the proxy is correctly set up in `my-voice-assistant/package.json`
3. Try accessing the test endpoint directly: http://localhost:3000/api/test
4. Restart both servers and clear your browser cache

## How It Works

- The React development server uses a proxy setting to forward API requests to the Flask backend
- React runs on port 3000, Flask runs on port 5001
- When you make a request to `/api/voice` from the browser, it's automatically forwarded to http://localhost:5001/api/voice
- This avoids CORS issues during development

## API Endpoints

- `/api/test` - Simple test endpoint that always works, good for debugging
- `/api/debug` - Returns information about the API
- `/api/text` - Text-only responses
- `/api/voice` - Voice responses with Kokoro

## Additional Notes

- When deployed to Render, different configuration is used (see render.yaml)
- Local development should use the dev setup described above 