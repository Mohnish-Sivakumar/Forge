#!/bin/bash
# Exit on error
set -e

echo "==> Starting render-build.sh script"

# Set Python version
export PYTHON_VERSION=3.12.9
echo "==> Using Python version: $PYTHON_VERSION"

# Install backend dependencies
echo "==> Installing Python dependencies"
pip install --upgrade pip

# Install dependencies with more detailed output
echo "==> Installing requirements from requirements-render.txt"
pip install -r requirements-render.txt -v || {
  echo "==> Warning: Failed to install from requirements-render.txt, using fallback"
  pip install flask==2.2.3 flask-cors==3.0.10 werkzeug==2.2.3 google-generativeai==0.3.1 gunicorn==20.1.0 requests>=2.28.0 numpy>=1.22.0
}

# Set environment variables for deployment
export ESSENTIAL_VOICES_ONLY=true
export SERVE_STATIC=true

# Build the frontend
echo "==> Building React frontend"
cd my-voice-assistant
npm install
npm run build:render
cd ..

# Set up static file serving from the backend
echo "==> Setting up static file serving"

# Check if backend directory exists
if [ -d "backend" ]; then
  echo "==> Using backend directory"
  
  # Create a directory for static files if it doesn't exist
  mkdir -p backend/static
  
  # Copy built frontend files to backend/static
  cp -r my-voice-assistant/build/* backend/static/
else
  echo "==> Using api directory (backend not found)"
  
  # Create a directory for static files if it doesn't exist
  mkdir -p api/static
  
  # Copy built frontend files to api/static
  cp -r my-voice-assistant/build/* api/static/
fi

echo "==> Checking Python installation:"
which python
python --version

echo "==> Build completed successfully" 