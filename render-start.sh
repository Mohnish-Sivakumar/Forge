#!/bin/bash
# This is a simplified start script for Render deployment

# Set environment variables
export SERVE_STATIC=true

# Clean up unnecessary files to save space
echo "==> Cleaning up to save storage space..."
rm -rf .git .github __pycache__ *.log *.gz
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete
find . -name "*.pyd" -delete
find . -name ".DS_Store" -delete
du -sh .

# Install dependencies - only what's needed
echo "==> Installing required packages..."
pip install flask==2.2.3 werkzeug==2.2.3 flask-cors==3.0.10 google-generativeai==0.3.1 kokoro==0.9.4

# Print debug information
echo "==> Python version: $(python --version)"
echo "==> Disk usage after cleanup:"
du -sh . /tmp

# Create a simple bootstrap script
cat > bootstrap.py << 'EOF'
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logging.info("Starting application bootstrap...")

# Test import dependencies
try:
    import flask
    import werkzeug
    import kokoro
    import google.generativeai as genai
    
    print(f"==> Flask version: {flask.__version__}")
    print(f"==> Werkzeug version: {werkzeug.__version__}")
    print(f"==> Kokoro imported successfully")
    print(f"==> Google Generative AI imported successfully")
except ImportError as e:
    print(f"==> IMPORT ERROR: {e}")
    sys.exit(1)

# Then try to import our app
try:
    from backend.app import app
    print("==> Successfully imported app")
except Exception as e:
    print(f"==> APP IMPORT ERROR: {e}")
    raise

# Start the server
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"==> Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
EOF

# Run the bootstrap script
echo "==> Starting application with direct Python..."
python bootstrap.py 