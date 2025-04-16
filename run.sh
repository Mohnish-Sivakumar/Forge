#!/bin/bash

# Export environment variables
export SERVE_STATIC=true

# Start the app
gunicorn backend.app:app --bind 0.0.0.0:$PORT
