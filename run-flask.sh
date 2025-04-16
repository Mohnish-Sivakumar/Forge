#!/bin/bash

# Export environment variables
export SERVE_STATIC=true
export PYTHON_VERSION=3.12.9
export FLASK_APP=backend/app.py

# Install dependencies again to make sure they're available
pip install -r requirements.txt

# Print Python path and installed packages for debugging
echo "==> Python path: $(which python)"
echo "==> Python version: $(python --version)"
echo "==> Installed packages:"
pip list

echo "==> Starting application with Flask"
cd backend && python -m flask run --host=0.0.0.0 --port=$PORT 