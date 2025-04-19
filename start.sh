#!/bin/bash
# Start script for Render

echo "==> Starting application on Render"

# Set environment variables
export ESSENTIAL_VOICES_ONLY=true
export FLASK_ENV=production
export SERVE_STATIC=true
export PYTHON_VERSION=3.12.9

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

# Check for Node.js static server fallback option
if [ "$USE_STATIC_SERVER" = "true" ]; then
  echo "==> Starting static server with Node.js"
  exec node static-server.js
fi

# If app.py exists in current directory, use it
if [ -f "app.py" ]; then
  echo "==> Starting app.py in current directory"
  exec gunicorn app:app --log-file=- --bind 0.0.0.0:$PORT --workers 2 --timeout 120
# If app.py exists in backend directory, use it
elif [ -f "backend/app.py" ]; then
  echo "==> Starting app.py in backend directory"
  cd backend
  exec gunicorn app:app --log-file=- --bind 0.0.0.0:$PORT --workers 2 --timeout 120
# Check for our new handler.py file first
elif [ -f "api/handler.py" ]; then
  echo "==> Using api/handler.py WSGI adapter"
  export PYTHONPATH=$PYTHONPATH:$(pwd)
  exec gunicorn --timeout 120 api.handler:app --log-file=- --bind 0.0.0.0:$PORT --workers 2
# Otherwise, try to use api/index.py
elif [ -f "api/index.py" ]; then
  echo "==> Using api/index.py as fallback"
  cd api
  if command -v uvicorn &> /dev/null; then
    exec gunicorn -k uvicorn.workers.UvicornWorker --timeout 120 handler:app --log-file=- --bind 0.0.0.0:$PORT
  else
    exec gunicorn --timeout 120 handler:app --log-file=- --bind 0.0.0.0:$PORT
  fi
# If all else fails, use the static server
else
  echo "==> No Python app found, falling back to static server"
  exec node static-server.js
fi 