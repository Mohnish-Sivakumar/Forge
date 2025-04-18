#!/bin/bash
# Exit on error
set -e

echo "Starting build process..."

# Set Python version
echo "Setting up Python environment..."
echo "python-3.9" > runtime.txt

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies for Express server
echo "Installing root Node.js dependencies for Express server..."
npm install

# Build React app
echo "Building React application..."
cd my-voice-assistant
npm install
npm run build
cd ..

# Create a backup of the build directory at the project root
echo "==> Creating backup of build directory at project root..."
if [ -d "my-voice-assistant/build" ]; then
  # Remove any existing backup
  if [ -d "build_backup" ]; then
    rm -rf build_backup
  fi
  # Make a copy of the build directory
  cp -r my-voice-assistant/build build_backup
  echo "  ✅ Backup created at ./build_backup"
  # List the backup directory to verify
  ls -la build_backup
else
  echo "  ❌ No build directory to backup"
fi

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

echo "Build process completed successfully." 