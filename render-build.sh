#!/usr/bin/env bash
# Exit on error
set -o errexit

# Initial setup
echo "==> Running build script..."

# Clean up unnecessary files to save space
echo "==> Initial cleanup to save storage space..."
rm -rf .git .github __pycache__ *.log *.gz
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete
find . -name "*.pyd" -delete
find . -name ".DS_Store" -delete
du -sh .

# Python packages - fresh setup
echo "==> Setting up Python environment (minimal installation)..."
pip install --upgrade pip
pip install --no-cache-dir flask==2.2.3 werkzeug==2.2.3 flask-cors==3.0.10 google-generativeai==0.3.1 kokoro==0.9.4

# Print installed packages for debugging
echo "==> Installed packages:"
pip list

# Install node and build the frontend
echo "==> Building frontend..."
cd my-voice-assistant
npm install --no-optional
npm run build
# Clean up node_modules to save space
rm -rf node_modules
cd ..

# Final cleanup
echo "==> Final cleanup to save space..."
rm -rf myenv venv StyleTTS2 .vercel

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

logging.basicConfig(level=logging.INFO)
logging.info("Starting application server...")

# Import the app
try:
    from backend.app import app
    print("==> Successfully imported app")
except Exception as e:
    print(f"==> ERROR: {e}")
    sys.exit(1)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"==> Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
EOSPY

# Start the server
python server.py
EOF

chmod +x start.sh

echo "==> Final disk usage:"
du -sh .

echo "==> Build completed!" 