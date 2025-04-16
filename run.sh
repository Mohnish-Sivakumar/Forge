#!/bin/bash

# Set up the environment
export SERVE_STATIC=true
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Install dependencies
pip install -r requirements.txt

# Print diagnostic info
echo "==> Python version: $(python --version)"
echo "==> Installed packages:"
pip list

# Check if Kokoro is installed properly
echo "==> Checking Kokoro installation..."
python -c "try:
    from kokoro import KPipeline
    print('Kokoro is available')
    try:
        pipeline = KPipeline()
        print('Kokoro pipeline initialized successfully')
    except Exception as e:
        print(f'Failed to initialize KPipeline: {e}')
except ImportError as e:
    print(f'Kokoro import error: {e}')"

# Start the application
cd backend
python -m flask run --host=0.0.0.0 --port=${PORT:-5000}
