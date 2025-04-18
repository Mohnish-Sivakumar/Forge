#!/bin/bash
# Start script for Render

echo "==> Starting application on Render"

# Set environment variables
export ESSENTIAL_VOICES_ONLY=true
export FLASK_ENV=production
export SERVE_STATIC=true

# Verify environment
echo "==> Verifying environment"
python verify-env.py

echo "==> Starting application with gunicorn"
exec gunicorn app:app --log-file=- --bind 0.0.0.0:$PORT 