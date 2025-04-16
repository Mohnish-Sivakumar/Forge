#!/bin/bash

# Export environment variables
export SERVE_STATIC=true
export PYTHON_VERSION=3.12.9

# Install dependencies
pip install -r requirements.txt

# Create a Python launcher script
cat > launcher.py << 'EOPY'
import os
import sys
from backend.app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
EOPY

# Run the Python script directly
echo "==> Starting application with Python"
python launcher.py 