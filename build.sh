#!/bin/bash
# Exit on error
set -e

echo "==== Build Script Starting ===="

# Install Python dependencies
echo "==> Installing Python dependencies..."
pip install -r requirements.txt

# Install and build React app
echo "==> Building React frontend..."
cd my-voice-assistant
npm install
# Force build to continue even with warnings
CI=false npm run build
cd ..

# Verify the build
echo "==> Verifying build artifacts..."
if [ -d "my-voice-assistant/build" ]; then
  echo "  ✅ React build directory exists"
  
  # Check static directories
  if [ -d "my-voice-assistant/build/static/js" ] && [ -d "my-voice-assistant/build/static/css" ]; then
    echo "  ✅ Static directories exist"
    
    # List JS and CSS files
    echo "  JS files:"
    ls -la my-voice-assistant/build/static/js/*.js
    
    echo "  CSS files:"
    ls -la my-voice-assistant/build/static/css/*.css
  else
    echo "  ❌ Static directories missing"
    echo "  Directory structure:"
    find my-voice-assistant/build -type d | sort
  fi
else
  echo "  ❌ Build directory missing"
  echo "  Current directory structure:"
  ls -la my-voice-assistant
fi

# Make sure start script is executable
echo "==> Making scripts executable..."
chmod +x start.sh

echo "==== Build Complete ====" 