#!/bin/bash

# Export environment variables
export SERVE_STATIC=true
export PYTHON_VERSION=3.12.9
export SPEECHIFY_API_KEY="fwsjj7SjBEmJ9C058GN5NLEEIfwOga3tYKkftbo_TQE="
export GEMINI_API_KEY="AIzaSyDrxMRoQ-Knm7gM_6YNHAiPhXoC6HN09S4"

# Fix dependency issues by removing problematic packages first
pip uninstall -y flask werkzeug

# Install dependencies with specific versions
pip install flask==2.2.3 flask-cors==3.0.10 werkzeug==2.2.3 google-generativeai==0.3.1 gunicorn==20.1.0 requests>=2.28.0 psutil>=5.9.0

# Print Python path and installed packages for debugging
echo "==> Python path: $(which python)"
echo "==> Python version: $(python --version)"
echo "==> Installed packages:"
pip list

# Create a simple Python script to test imports
cat > test_imports.py << 'EOF'
import flask
import werkzeug
import google.generativeai
print(f"Flask version: {flask.__version__}")
print(f"Werkzeug version: {werkzeug.__version__}")
EOF

echo "==> Testing imports:"
python test_imports.py

# Try to use gunicorn directly
echo "==> Starting application with gunicorn"
gunicorn backend.app:app --bind 0.0.0.0:$PORT

# If gunicorn fails, try running with Python directly
if [ $? -ne 0 ]; then
    echo "==> Gunicorn failed, trying direct Python approach"
    # Create a simple server script
    cat > simple_server.py << 'EOF'
import os
from backend.app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"==> Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
EOF
    # Run the simple server
    python simple_server.py
fi
