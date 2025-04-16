#!/bin/bash

# Export environment variables
export SERVE_STATIC=true
export PYTHON_VERSION=3.12.9

# Fix dependency issues by removing problematic packages first
pip uninstall -y flask werkzeug
# Then install with the correct versions including Kokoro
pip install flask==2.2.3 flask-cors==3.0.10 werkzeug==2.2.3 google-generativeai==0.3.1 gunicorn==20.1.0 kokoro==0.2.1 soundfile==0.12.1 numpy>=1.20.0

# Print debug information
echo "==> Python path: $(which python)"
echo "==> Python version: $(python --version)"
echo "==> Installed packages:"
pip list

# Create a Python launcher script
cat > launcher.py << 'EOPY'
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logging.info("Starting server...")

# Make sure our dependencies are available
try:
    import flask
    from flask import Flask, request, jsonify
    print(f"==> Flask version: {flask.__version__}")
    import werkzeug
    print(f"==> Werkzeug version: {werkzeug.__version__}")
    
    # Try to import Kokoro
    try:
        from kokoro import KPipeline
        print("==> Kokoro TTS is available")
    except ImportError as e:
        print(f"==> Kokoro import error: {e}")
    except Exception as e:
        print(f"==> Error initializing Kokoro: {e}")
        
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