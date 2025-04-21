#!/usr/bin/env bash
# Exit on error
set -o errexit

# Initial setup
echo "==> Running build script..."

# Set environment variables
export SPEECHIFY_API_KEY="fwsjj7SjBEmJ9C058GN5NLEEIfwOga3tYKkftbo_TQE="
export GEMINI_API_KEY="AIzaSyDrxMRoQ-Knm7gM_6YNHAiPhXoC6HN09S4"
export SERVE_STATIC=true

# Python packages - fresh setup with specific versions
echo "==> Setting up Python environment..."
pip install --upgrade pip
pip install --no-cache-dir flask==2.2.3 werkzeug==2.2.3 flask-cors==3.0.10 google-generativeai==0.3.1 gunicorn==20.1.0 requests>=2.28.0 psutil>=5.9.0

# Print installed packages for debugging
echo "==> Installed packages:"
pip list

# Install node and build the frontend
echo "==> Building frontend..."
cd my-voice-assistant
npm install
DISABLE_ESLINT_PLUGIN=true CI=false npm run build
cd ..

# Create the startup script
echo "==> Creating start.sh script..."
cat > start.sh << 'EOF'
#!/bin/bash

# Set environment variables
export SERVE_STATIC=true
export PYTHONUNBUFFERED=1
export SPEECHIFY_API_KEY="fwsjj7SjBEmJ9C058GN5NLEEIfwOga3tYKkftbo_TQE="
export GEMINI_API_KEY="AIzaSyDrxMRoQ-Knm7gM_6YNHAiPhXoC6HN09S4"

# Install dependencies with specific versions
pip install flask==2.2.3 flask-cors==3.0.10 werkzeug==2.2.3 google-generativeai==0.3.1 gunicorn==20.1.0 requests>=2.28.0 psutil>=5.9.0

# Print Python and package info
echo "==> Python version: $(python --version)"
echo "==> Installed packages:"
pip list

# Start gunicorn with combined backend/frontend
echo "==> Starting application with gunicorn..."
cd backend && gunicorn app:app --bind 0.0.0.0:$PORT --workers=1 --threads=2 --timeout=120
EOF

chmod +x start.sh

echo "==> Build completed!" 