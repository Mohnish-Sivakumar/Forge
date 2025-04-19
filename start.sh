#!/bin/bash
# Start script for Render

echo "==> Starting application on Render"

# Set environment variables
export ESSENTIAL_VOICES_ONLY=true
export FLASK_ENV=production
export SERVE_STATIC=true
export PYTHON_VERSION=3.12.9
export PYTHONUNBUFFERED=1 # Ensure real-time logging

# Check if GEMINI_API_KEY is set but GOOGLE_API_KEY is not
if [ -n "$GEMINI_API_KEY" ] && [ -z "$GOOGLE_API_KEY" ]; then
  echo "==> Copying GEMINI_API_KEY to GOOGLE_API_KEY for compatibility"
  export GOOGLE_API_KEY=$GEMINI_API_KEY
fi

# Print environment info
echo "==> Python version: $(python --version)"
echo "==> Current directory: $(pwd)"
echo "==> API Keys: GOOGLE_API_KEY=$(if [ -n "$GOOGLE_API_KEY" ]; then echo "is set"; else echo "not set"; fi), GEMINI_API_KEY=$(if [ -n "$GEMINI_API_KEY" ]; then echo "is set"; else echo "not set"; fi)"
echo "==> Verifying environment"
python verify-env.py

# Create the simplified server approach
if [ -f "simple_server.py" ]; then
  echo "==> Using simple_server.py (recommended)"
  exec gunicorn simple_server:app --log-file=- --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile -
  exit 0
fi

# The rest is fallback if simple_server.py doesn't exist or fails

# Ensure api/static directory exists and has the frontend files
if [ ! -d "api/static" ]; then
  echo "==> Creating api/static directory"
  mkdir -p api/static
  
  # Copy from my-voice-assistant/build if it exists
  if [ -d "my-voice-assistant/build" ]; then
    echo "==> Copying files from my-voice-assistant/build to api/static"
    cp -r my-voice-assistant/build/* api/static/
    if [ -d "my-voice-assistant/build/static" ]; then
      mkdir -p api/static/static
      cp -r my-voice-assistant/build/static/* api/static/static/
    fi
  # Otherwise copy from backend/static if it exists
  elif [ -d "backend/static" ]; then
    echo "==> Copying files from backend/static to api/static"
    cp -r backend/static/* api/static/
  fi
fi

# Print static file info
echo "==> Static file directories:"
if [ -d "backend/static" ]; then
  echo "backend/static exists with files:"
  ls -la backend/static
  if [ -d "backend/static/static" ]; then
    echo "backend/static/static exists with files:"
    ls -la backend/static/static
  fi
fi
if [ -d "api/static" ]; then
  echo "api/static exists with files:"
  ls -la api/static
  if [ -d "api/static/static" ]; then
    echo "api/static/static exists with files:"
    ls -la api/static/static
  fi
fi

# Create a minimal index.html if none exists
if [ ! -f "api/static/index.html" ]; then
  echo "==> Creating minimal index.html in api/static"
  mkdir -p api/static
  cat > api/static/index.html << 'EOL'
<!DOCTYPE html>
<html>
<head>
  <title>Voice Assistant</title>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
    h1 { color: #333; }
    .container { max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Voice Assistant</h1>
    <p>The Voice Assistant API is running. Please use a frontend client to interact with it.</p>
    <p>API endpoints available:</p>
    <ul>
      <li><code>/api/text</code> - Text generation</li>
      <li><code>/api/voice</code> - Voice generation</li>
      <li><code>/api/debug</code> - Debug information</li>
    </ul>
  </div>
</body>
</html>
EOL
fi

# Try to start the API server
# Check for our new handler.py file first
if [ -f "api/handler.py" ]; then
  echo "==> Using api/handler.py WSGI adapter"
  export PYTHONPATH=$PYTHONPATH:$(pwd)
  exec gunicorn --timeout 120 api.handler:app --log-file=- --bind 0.0.0.0:$PORT --workers 2
# If app.py exists in current directory, use it
elif [ -f "app.py" ]; then
  echo "==> Starting app.py in current directory"
  exec gunicorn app:app --log-file=- --bind 0.0.0.0:$PORT --workers 2 --timeout 120
# If app.py exists in backend directory, use it
elif [ -f "backend/app.py" ]; then
  echo "==> Starting app.py in backend directory"
  cd backend
  exec gunicorn app:app --log-file=- --bind 0.0.0.0:$PORT --workers 2 --timeout 120
# Otherwise, try to use api/index.py
elif [ -f "api/index.py" ]; then
  echo "==> Using api/index.py as fallback"
  cd api
  if command -v uvicorn &> /dev/null; then
    exec gunicorn -k uvicorn.workers.UvicornWorker --timeout 120 handler:app --log-file=- --bind 0.0.0.0:$PORT
  else
    exec gunicorn --timeout 120 handler:app --log-file=- --bind 0.0.0.0:$PORT
  fi
# If all fails, check if static server is explicitly requested
elif [ "$USE_STATIC_SERVER" = "true" ]; then
  echo "==> Starting static server with Node.js (explicitly requested)"
  exec node static-server.js
# Otherwise, use static server as a last resort
else
  echo "==> No Python app found, falling back to static server"
  exec node static-server.js
fi 