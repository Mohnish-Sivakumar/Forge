#!/usr/bin/env bash
# Exit on error
set -o errexit

# Initial setup
echo "==> Running build script..."

# Python packages - fresh setup with CPU-only versions
echo "==> Setting up Python environment..."
pip install --upgrade pip
pip install --no-cache-dir flask==2.2.3 werkzeug==2.2.3 flask-cors==3.0.10 google-generativeai==0.3.1 gunicorn==20.1.0 psutil>=5.9.0
pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu torch==2.6.0+cpu
pip install --no-cache-dir numpy>=1.22.0
pip install --no-cache-dir kokoro==0.9.4

# Print installed packages for debugging
echo "==> Installed packages:"
pip list

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
export MAX_MEMORY_MB=400
export PYTHONUNBUFFERED=1

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
from api.index import handler
import http.server
from http.server import HTTPServer

if __name__ == '__main__':
    # Clean up memory
    import gc
    gc.collect()
    
    # Monitor memory if possible
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        print(f"==> Initial memory usage: {memory_mb:.2f} MB")
    except ImportError:
        print("==> psutil not available, cannot monitor memory")
    
    # Start the server
    port = int(os.environ.get('PORT', 10000))
    print(f"==> Starting server on port {port}")
    server = HTTPServer(('0.0.0.0', port), handler)
    server.serve_forever()
EOSPY

# Start the server
python server.py
EOF

chmod +x start.sh

echo "==> Build completed!" 