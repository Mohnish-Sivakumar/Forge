#!/bin/bash

# Export environment variables
export SERVE_STATIC=true
export PYTHON_VERSION=3.12.9

# Start the app
gunicorn backend.app:app --bind 0.0.0.0:$PORT
