#!/bin/bash

# Set environment variables
export PORT=${PORT:-10000}
export MAX_MEMORY_MB=400
export PYTHONUNBUFFERED=1

# Print memory information
echo "==> Available memory info:"
free -m || echo "free command not available"

# Create a simplified server script
cat > server.py << 'EOPY'
import os
import sys
import logging
from http.server import HTTPServer
from api.index import handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_server(port=10000):
    """Run the HTTP server on the specified port"""
    try:
        server = HTTPServer(('0.0.0.0', port), handler)
        logger.info(f"Starting server on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Get port from environment variable
    port = int(os.environ.get('PORT', 10000))
    
    # Report memory usage if psutil is available
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        logger.info(f"Initial memory usage: {memory_mb:.2f} MB")
        
        # Set memory limit
        max_memory_mb = float(os.environ.get('MAX_MEMORY_MB', 400))
        logger.info(f"Memory limit set to {max_memory_mb} MB")
    except ImportError:
        logger.warning("psutil not available, cannot monitor memory usage")
    
    # Start server
    run_server(port)
EOPY

# Run the server
echo "==> Starting server on port $PORT"
export PYTHONPATH=$PYTHONPATH:$(pwd)
python server.py 