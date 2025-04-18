#!/bin/bash

# Set environment variables
export LOW_MEMORY_MODE=true
export FLASK_ENV=production
export NODE_ENV=production

echo "Starting application in low memory mode..."
echo "Loading optimization flags..."

# Clear Python cache files to save memory
echo "Cleaning up cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete

# Install required Node.js dependencies if they're not already installed
if [ ! -d "node_modules" ]; then
  echo "Installing Express dependencies..."
  npm install express http-proxy-middleware
fi

# Start the Express server (which will start Flask in a child process)
echo "Starting Express server..."
node server.js 