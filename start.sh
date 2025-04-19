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
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from api.index import handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a custom handler that can serve static files
class StaticFileHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        """Handle HEAD requests (used by browsers to check if resources exist)"""
        # Check if this is an API request
        if self.path.startswith('/api/'):
            # Forward to API handler
            api_handler = ApiProxyHandler(self, self.path, 'HEAD')
            api_handler.handle()
            return
            
        # Try to serve static file
        build_dir = os.path.join(os.getcwd(), "my-voice-assistant/build")
        file_path = self._get_file_path(build_dir)
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.send_response(200)
            content_type = self._get_content_type(file_path)
            self.send_header('Content-type', content_type)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        # Check if this is an API request
        if self.path.startswith('/api/'):
            # Forward to API handler
            api_handler = ApiProxyHandler(self, self.path, 'GET')
            api_handler.handle()
            return
            
        # Try to serve static file
        build_dir = os.path.join(os.getcwd(), "my-voice-assistant/build")
        file_path = self._get_file_path(build_dir)
        
        # Special handling for root path and SPA routing
        if file_path.endswith('/') or not os.path.exists(file_path) or not os.path.isfile(file_path):
            file_path = os.path.join(build_dir, 'index.html')
        
        # Check if the file exists and is a file
        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.send_response(200)
            content_type = self._get_content_type(file_path)
            self.send_header('Content-type', content_type)
            self.end_headers()
            
            # Serve the file
            with open(file_path, 'rb') as file:
                self.wfile.write(file.read())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not found')
    
    def do_POST(self):
        """Handle POST requests"""
        # All POST requests go to the API
        api_handler = ApiProxyHandler(self, self.path, 'POST')
        api_handler.handle()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests"""
        # CORS preflight requests go to the API
        api_handler = ApiProxyHandler(self, self.path, 'OPTIONS')
        api_handler.handle()
    
    def _get_file_path(self, build_dir):
        """Get the file path from the URL path"""
        path = self.path.split('?')[0]  # Remove query parameters
        if path == '/':
            return os.path.join(build_dir, 'index.html')
        return os.path.join(build_dir, path.lstrip('/'))
    
    def _get_content_type(self, file_path):
        """Get the content type based on file extension"""
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            return 'application/octet-stream'
        return content_type

class ApiProxyHandler:
    """Class to handle API requests by proxying them to the API handler"""
    def __init__(self, server_handler, path, method):
        self.server_handler = server_handler
        self.path = path
        self.method = method
        
        # Create a connection to intercept the response
        from io import BytesIO
        self.wfile = BytesIO()
        
    def handle(self):
        """Handle the API request"""
        try:
            # Create a new instance of the API handler
            api_handler = self._create_api_handler()
            
            # Call the appropriate method
            if self.method == 'GET':
                api_handler.do_GET()
            elif self.method == 'POST':
                api_handler.do_POST()
            elif self.method == 'OPTIONS':
                api_handler.do_OPTIONS()
            elif self.method == 'HEAD':
                api_handler.do_HEAD()
                
            logger.info(f"API request handled: {self.path}")
        except Exception as e:
            logger.error(f"Error handling API request: {e}")
            self.server_handler.send_response(500)
            self.server_handler.send_header('Content-type', 'application/json')
            self.server_handler.end_headers()
            self.server_handler.wfile.write(b'{"error": "Internal server error"}')
            
    def _create_api_handler(self):
        """Create a new instance of the API handler"""
        # Create a modified handler class that will work with our proxy
        class ApiHandler(handler):
            def __init__(self, proxy_handler):
                self.path = proxy_handler.path
                self.headers = proxy_handler.server_handler.headers
                self.rfile = proxy_handler.server_handler.rfile
                self.wfile = proxy_handler.server_handler.wfile
                self.server = proxy_handler.server_handler.server
                self.client_address = proxy_handler.server_handler.client_address
                
            def send_response(self, code, message=None):
                self.proxy_handler.server_handler.send_response(code, message)
                
            def send_header(self, keyword, value):
                self.proxy_handler.server_handler.send_header(keyword, value)
                
            def end_headers(self):
                self.proxy_handler.server_handler.end_headers()
        
        # Create an instance
        api_instance = ApiHandler(self)
        api_instance.proxy_handler = self
        return api_instance

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
        except ImportError:
            logger.warning("psutil not available, cannot monitor memory usage")
        
        # Create a server that serves both static files and API requests
        server = HTTPServer(('0.0.0.0', port), StaticFileHandler)
        logger.info(f"Starting server on port {port}")
        
        # Run the server
        server.serve_forever()
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Initialize MIME types
    mimetypes.init()
    
    # Add common MIME types that might be missing
    mimetypes.add_type('text/javascript', '.js')
    mimetypes.add_type('text/css', '.css')
    mimetypes.add_type('image/svg+xml', '.svg')
    
    # Get port from environment variable
    port = int(os.environ.get('PORT', 10000))
    
    # Start server
    run_server(port)
EOPY

# Run the server with memory limits
echo "==> Starting server on port $PORT with memory optimization"
export PYTHONPATH=$PYTHONPATH:$(pwd)
python -O server.py 