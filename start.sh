#!/bin/bash
# Start script for Render

echo "==> Starting application on Render"

# Set environment variables
export ESSENTIAL_VOICES_ONLY=true
export FLASK_ENV=production
export SERVE_STATIC=true
export PYTHON_VERSION=3.12.9

# Print environment info
echo "==> Python version: $(python --version)"
echo "==> Current directory: $(pwd)"
echo "==> Verifying environment"
python verify-env.py

# Check if we have app.py in current directory or backend directory
if [ -f "app.py" ]; then
  echo "==> Starting app.py in current directory"
  exec gunicorn app:app --log-file=- --bind 0.0.0.0:$PORT
elif [ -f "backend/app.py" ]; then
  echo "==> Starting app.py in backend directory"
  cd backend
  exec gunicorn app:app --log-file=- --bind 0.0.0.0:$PORT
else
  echo "==> Using api/index.py as fallback"
  cd api
  exec gunicorn -k uvicorn.workers.UvicornWorker --timeout 120 handler:app --log-file=- --bind 0.0.0.0:$PORT
fi 