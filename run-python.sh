#!/bin/bash

# Export environment variables
export SERVE_STATIC=true
export PYTHON_VERSION=3.12.9

# Fix dependency issues by removing problematic packages first
pip uninstall -y flask werkzeug
# Then install with the correct versions
pip install -r requirements.txt

# Print debug information
echo "==> Python path: $(which python)"
echo "==> Python version: $(python --version)"
echo "==> Installed packages:"
pip list

# Create a Python launcher script
cat > launcher.py << 'EOPY'
import os
import sys

# Make sure our dependencies are available
try:
    import flask
    from flask import Flask, request, jsonify
    print(f"==> Flask version: {flask.__version__}")
    import werkzeug
    print(f"==> Werkzeug version: {werkzeug.__version__}")
except ImportError as e:
    print(f"==> Error importing dependencies: {e}")
    sys.exit(1)

# Now import our app
try:
    from backend.app import app
    print("==> Successfully imported app")
except Exception as e:
    print(f"==> Error importing app: {e}")
    raise

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"==> Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
EOPY

# Run the Python script directly
echo "==> Starting application with Python"
python launcher.py 