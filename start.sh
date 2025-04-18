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

# Start the Flask app using gunicorn with minimal workers
echo "==> Starting with minimal gunicorn workers..."
gunicorn backend.app:app --bind 0.0.0.0:$PORT --workers=1 --threads=2 --timeout=60 