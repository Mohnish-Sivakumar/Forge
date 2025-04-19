#!/bin/bash

# Set environment variables
export PORT=${PORT:-10000}
export MAX_MEMORY_MB=400
export PYTHONUNBUFFERED=1
export PYTHONOPTIMIZE=1  # Reduces memory by disabling debug features

# Print memory information
echo "==> Available memory info:"
free -m || echo "free command not available"

# Perform garbage collection before starting
echo "==> Cleaning memory before start"
python -c "import gc; gc.collect()" || echo "GC not available"

# Create a simplified server script with memory optimizations
cat > server.py << 'EOPY'
import os
import sys
import logging
import gc
from http.server import HTTPServer
from api.index import handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_server(port=10000):
    """Run the HTTP server on the specified port with memory optimizations"""
    try:
        # Force garbage collection before starting
        gc.collect()
        
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
            
            # Setup a periodic memory check
            def check_memory():
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                logger.info(f"Current memory usage: {memory_mb:.2f} MB")
                if memory_mb > max_memory_mb * 0.9:
                    logger.warning(f"Memory usage high: {memory_mb:.2f} MB")
                    gc.collect()
        except ImportError:
            logger.warning("psutil not available, cannot monitor memory usage")
        
        # Start server
        server = HTTPServer(('0.0.0.0', port), handler)
        logger.info(f"Starting server on port {port}")
        
        # Run the server
        server.serve_forever()
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Get port from environment variable
    port = int(os.environ.get('PORT', 10000))
    
    # Start server
    run_server(port)
EOPY

# Run the server with memory limits
echo "==> Starting server on port $PORT with memory optimization"
export PYTHONPATH=$PYTHONPATH:$(pwd)
python -O server.py 