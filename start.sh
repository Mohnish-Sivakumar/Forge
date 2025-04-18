#!/bin/bash

# Set environment variables for low memory mode
export LOW_MEMORY_MODE=true
export SERVE_STATIC=true
export FLASK_ENV=production

# Make sure memory usage doesn't exceed limits
echo "==> Starting app in low memory mode"
echo "==> Setting memory optimization flags..."

# Remove any cached Python files to save memory
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Print some debug info about the build directories
echo "==> Checking build directories..."
echo "Current directory: $(pwd)"

# Check primary build directory
if [ -d "my-voice-assistant/build" ]; then
  echo "  ✅ Primary build directory exists"
  echo "  Static files:"
  ls -la my-voice-assistant/build/static
  
  # Check for JS and CSS files
  if [ -d "my-voice-assistant/build/static/js" ]; then
    echo "  ✅ JS directory exists:"
    ls -la my-voice-assistant/build/static/js
  else
    echo "  ❌ JS directory missing"
  fi
  
  if [ -d "my-voice-assistant/build/static/css" ]; then
    echo "  ✅ CSS directory exists:"
    ls -la my-voice-assistant/build/static/css
  else
    echo "  ❌ CSS directory missing"
  fi
else
  echo "  ❌ Primary build directory missing"
fi

# Check backup build directory
if [ -d "build_backup" ]; then
  echo "  ✅ Backup build directory exists"
  echo "  Static files:"
  ls -la build_backup/static
  
  # Check for JS and CSS files
  if [ -d "build_backup/static/js" ]; then
    echo "  ✅ Backup JS directory exists:"
    ls -la build_backup/static/js
  else
    echo "  ❌ Backup JS directory missing"
  fi
  
  if [ -d "build_backup/static/css" ]; then
    echo "  ✅ Backup CSS directory exists:"
    ls -la build_backup/static/css
  else
    echo "  ❌ Backup CSS directory missing"
  fi
else
  echo "  ❌ Backup build directory missing"
fi

# Check for alternative locations that Render might use
for path in "/opt/render/project/src/my-voice-assistant/build" "/app/my-voice-assistant/build"; do
  if [ -d "$path" ]; then
    echo "  ✅ Build directory found at $path"
    ls -la "$path/static"
  fi
done

# Start the Flask app using gunicorn with minimal workers
echo "==> Starting with minimal gunicorn workers..."
gunicorn backend.app:app --bind 0.0.0.0:$PORT --workers=1 --threads=2 --timeout=60 