#!/usr/bin/env bash
# Exit on error
set -o errexit

# Initial setup
echo "==> Running build script..."

# Run storage cleanup to stay within limits
echo "==> Running storage cleanup..."
python api/cleanup.py

# Python packages - fresh setup
echo "==> Setting up Python environment..."
pip install --upgrade pip
pip install flask==2.2.3 werkzeug==2.2.3 flask-cors==3.0.10 google-generativeai==0.3.1 gunicorn==20.1.0 kokoro==0.9.4

# Download only essential voice files
echo "==> Setting up essential voice files..."
mkdir -p api/voice_files
for voice in af_heart am_michael; do
  echo "Downloading $voice..."
  curl -sL "https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices/${voice}.pt" -o "api/voice_files/${voice}.pt"
done

# Print installed packages for debugging
echo "==> Installed packages:"
pip list

# Install node and build the frontend
echo "==> Building frontend..."
cd my-voice-assistant
npm install
npm run build
cd ..

# Run cleanup again after build to remove any temporary files created during build
echo "==> Final cleanup..."
python api/cleanup.py

# Create the startup script
cat > start.sh << 'EOF'
#!/usr/bin/env bash
export SERVE_STATIC=true
export FLASK_APP=backend/app.py

# Clean up any temporary files before starting
python api/cleanup.py

# Create a simple server.py
cat > server.py << 'EOSPY'
import os
import sys

# Check if required modules are available
try:
    import flask
    import werkzeug
    import kokoro
    print(f"==> Flask version: {flask.__version__}")
    print(f"==> Werkzeug version: {werkzeug.__version__}")
    print(f"==> Kokoro imported successfully")
except ImportError as e:
    print(f"==> ERROR: {e}")
    sys.exit(1)

# Import the app
from backend.app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"==> Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
EOSPY

# Start the server
python server.py
EOF

chmod +x start.sh

echo "==> Build completed!" 