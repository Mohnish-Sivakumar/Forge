#!/bin/bash
# This is a simplified start script for Render deployment

# Set environment variables
export SERVE_STATIC=true
export FLASK_ENV=production
export PYTHONUNBUFFERED=1  # This ensures logs are output immediately

# Install dependencies again as a safeguard
echo "==> Installing required packages..."
pip install flask==2.2.3 werkzeug==2.2.3 flask-cors==3.0.10 google-generativeai==0.3.1 kokoro==0.9.4

# Print debug information
echo "==> Python version: $(python --version)"
echo "==> Installed packages:"
pip list | grep -E 'flask|werkzeug|kokoro|google-generativeai'

# Check that static files exist
echo "==> Checking for React build files:"
ls -la ./my-voice-assistant/build
ls -la ./my-voice-assistant/build/static || echo "WARNING: No static directory found!"

# Create a more robust bootstrap script
cat > bootstrap.py << 'EOF'
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test import dependencies
try:
    import flask
    import werkzeug
    import kokoro
    import google.generativeai as genai
    
    logger.info(f"Flask version: {flask.__version__}")
    logger.info(f"Werkzeug version: {werkzeug.__version__}")
    logger.info("Kokoro imported successfully")
    logger.info("Google Generative AI imported successfully")
except ImportError as e:
    logger.error(f"IMPORT ERROR: {e}")
    sys.exit(1)

# Then try to import our app
try:
    from backend.app import app
    logger.info("Successfully imported app")
except Exception as e:
    logger.error(f"APP IMPORT ERROR: {e}")
    raise

# Start the server
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
EOF

# Run the bootstrap script
echo "==> Starting application with direct Python..."
python bootstrap.py 