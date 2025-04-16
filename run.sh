#!/bin/bash

# Exit on error
set -e

# Export environment variables
export SERVE_STATIC=true
export PYTHON_VERSION=3.12.9

echo "==> Installing base packages first to avoid dependency issues"
pip install --upgrade pip setuptools wheel

# Clean start - first time might fail, that's ok
pip uninstall -y flask werkzeug kokoro soundfile numpy || true

echo "==> Installing dependencies one by one to isolate any issues"
pip install flask==2.2.3
pip install werkzeug==2.2.3
pip install flask-cors==3.0.10
pip install google-generativeai==0.3.1
pip install gunicorn==20.1.0
pip install numpy==1.24.3
pip install soundfile==0.12.1
# Install Kokoro last
pip install kokoro==0.9.4

# Print Python path and installed packages for debugging
echo "==> Python path: $(which python)"
echo "==> Python version: $(python --version)"
echo "==> Installed packages:"
pip list

# Create a simple Python script to test imports
cat > test_imports.py << 'EOF'
import sys
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")

try:
    import flask
    print(f"Flask version: {flask.__version__}")
except ImportError as e:
    print(f"Error importing Flask: {e}")

try:
    import werkzeug
    print(f"Werkzeug version: {werkzeug.__version__}")
except ImportError as e:
    print(f"Error importing Werkzeug: {e}")

try:
    import kokoro
    print(f"Kokoro version: {kokoro.__version__}")
    print("Kokoro imported successfully")
except ImportError as e:
    print(f"Error importing Kokoro: {e}")

try:
    import soundfile
    import numpy
    print("Audio dependencies imported successfully")
except ImportError as e:
    print(f"Error importing audio dependencies: {e}")
EOF

echo "==> Testing imports:"
python test_imports.py

# Simple script to run the app
cat > run_app.py << 'EOF'
import os
import sys
import importlib

# Add the current directory to path to find modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import the app module
try:
    from backend.app import app
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port)
except Exception as e:
    print(f"Error starting app: {e}")
    sys.exit(1)
EOF

# Try to use gunicorn directly
echo "==> Trying to start with gunicorn"
which gunicorn || pip install gunicorn==20.1.0

# Try gunicorn, fallback to Python directly
if command -v gunicorn &> /dev/null; then
    echo "==> Starting with gunicorn"
    gunicorn backend.app:app --bind 0.0.0.0:$PORT
else
    echo "==> Gunicorn not found, starting with Python"
    python run_app.py
fi
