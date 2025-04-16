#!/usr/bin/env bash
# Exit on error
set -o errexit

# Initial setup
echo "==> Running build script..."

# Python packages - fresh setup
echo "==> Setting up Python environment..."
pip install --upgrade pip
pip install flask==2.2.3 werkzeug==2.2.3 flask-cors==3.0.10 google-generativeai==0.3.1 gunicorn==20.1.0 kokoro==0.2.1 soundfile==0.12.1 numpy>=1.20.0

# Install node and build the frontend
echo "==> Building frontend..."
cd my-voice-assistant
npm install
npm run build
cd ..

# Create the startup script
cat > start.sh << 'EOF'
#!/usr/bin/env bash
export SERVE_STATIC=true
export FLASK_APP=backend/app.py

# Create a simple server.py
cat > server.py << 'EOSPY'
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logging.info("Starting server...")

# Try to import Kokoro and check if it's available
try:
    from kokoro import KPipeline
    logging.info("Kokoro TTS is available")
except ImportError as e:
    logging.error(f"Kokoro import error: {e}")
except Exception as e:
    logging.error(f"Error initializing Kokoro: {e}")

# Import the Flask app
try:
    from backend.app import app
    logging.info("Successfully imported app")
except Exception as e:
    logging.error(f"Error importing app: {e}")
    raise

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logging.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
EOSPY

# Start the server
python server.py
EOF

chmod +x start.sh

echo "==> Build completed!" 