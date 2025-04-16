#!/bin/bash

# Set up the environment
export SERVE_STATIC=true
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Print diagnostic info
echo "==> Python version: $(python --version)"
echo "==> Node version: $(node --version)"
echo "==> Installed Python packages:"
pip list

# Install build essentials and necessary dependencies for Kokoro with Python 3.12
echo "==> Installing system dependencies for Kokoro..."
apt-get update && apt-get install -y build-essential libsndfile1

# Handle potential compatibility issues with Python 3.12.9
echo "==> Setting up Kokoro compatibility patches..."
# Create patch directory if needed
mkdir -p patches

# Check if Kokoro is installed properly
echo "==> Checking Kokoro installation..."
python -c "
import sys
print(f'Python version: {sys.version}')
try:
    from kokoro import KPipeline
    print('Kokoro is available')
    try:
        pipeline = KPipeline()
        print('Kokoro pipeline initialized successfully')
    except Exception as e:
        print(f'Failed to initialize KPipeline: {e}')
        # Try to fix common issues with Python 3.12
        print('Attempting compatibility fixes...')
        import os
        import site
        site_packages = site.getsitepackages()[0]
        print(f'Site packages directory: {site_packages}')
        kokoro_dir = os.path.join(site_packages, 'kokoro')
        if os.path.exists(kokoro_dir):
            print(f'Kokoro directory found at {kokoro_dir}')
except ImportError as e:
    print(f'Kokoro import error: {e}')
"

# Start the application using gunicorn
echo "==> Starting application with Gunicorn..."
gunicorn backend.app:app --bind 0.0.0.0:$PORT --log-level debug 