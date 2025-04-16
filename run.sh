#!/bin/bash

# Export environment variables
export SERVE_STATIC=true
export PYTHON_VERSION=3.12.9

# Fix dependency issues by removing problematic packages first
pip uninstall -y flask werkzeug

# Install dependencies with specific versions - include Kokoro
pip install flask==2.2.3 flask-cors==3.0.10 werkzeug==2.2.3 google-generativeai==0.3.1 gunicorn==20.1.0 kokoro==0.1.5 soundfile==0.12.1 numpy==1.24.3

# Print Python path and installed packages for debugging
echo "==> Python path: $(which python)"
echo "==> Python version: $(python --version)"
echo "==> Installed packages:"
pip list

# Create a simple Python script to test imports
cat > test_imports.py << 'EOF'
import flask
import werkzeug
print(f"Flask version: {flask.__version__}")
print(f"Werkzeug version: {werkzeug.__version__}")
try:
    import kokoro
    print("Kokoro imported successfully")
    import soundfile
    import numpy
    print("All TTS dependencies imported successfully")
except ImportError as e:
    print(f"Error importing Kokoro: {e}")
EOF

echo "==> Testing imports:"
python test_imports.py

# Try to use gunicorn directly
echo "==> Starting application with gunicorn"
gunicorn backend.app:app --bind 0.0.0.0:$PORT

# If gunicorn fails, try running with Python directly
if [ $? -ne 0 ]; then
    echo "==> Gunicorn failed, trying Python directly"
    export FLASK_APP=backend/app.py
    python -m flask run --host=0.0.0.0 --port=$PORT
fi
