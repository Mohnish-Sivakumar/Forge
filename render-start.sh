#!/bin/bash
# This is a simplified start script for Render deployment

# Set environment variables
export SERVE_STATIC=true

# Install dependencies again as a safeguard
echo "==> Installing required packages..."
pip install flask==2.2.3 werkzeug==2.2.3 flask-cors==3.0.10 google-generativeai==0.3.1 kokoro==0.9.4

# Print debug information
echo "==> Python version: $(python --version)"
echo "==> Installed packages:"
pip list | grep -E 'flask|werkzeug|kokoro|google-generativeai'

# Create a simple bootstrap script
cat > bootstrap.py << 'EOF'
import os
import sys

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