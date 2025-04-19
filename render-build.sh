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

# Create a small patch to the api/index.py file to add do_HEAD method
echo "==> Adding missing do_HEAD method to handler class..."
cat > patch_api.py << 'EOF'
import os

# Path to the file
file_path = 'api/index.py'

# Read the file content
with open(file_path, 'r') as file:
    content = file.read()

# Check if do_HEAD method already exists
if 'def do_HEAD(' not in content:
    # Find the class handler definition
    handler_class_pos = content.find('class handler(BaseHTTPRequestHandler):')
    if handler_class_pos != -1:
        # Find where to insert the do_HEAD method
        options_method_pos = content.find('def do_OPTIONS(self):', handler_class_pos)
        if options_method_pos != -1:
            # Insert do_HEAD method before do_OPTIONS
            head_method = """
    def do_HEAD(self):
        \"\"\"Handle HEAD requests\"\"\"
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
"""
            new_content = content[:options_method_pos] + head_method + content[options_method_pos:]
            
            # Write back to the file
            with open(file_path, 'w') as file:
                file.write(new_content)
            print(f"Added do_HEAD method to {file_path}")
        else:
            print("Could not find do_OPTIONS method position")
    else:
        print("Could not find handler class definition")
else:
    print("do_HEAD method already exists")
EOF

# Run the patch
python patch_api.py

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
    def __init__(self, *args, **kwargs):
        # Initialize BaseHTTPRequestHandler directly
        BaseHTTPRequestHandler.__init__(self, *args, **kwargs)
    
    def do_HEAD(self):
        """Handle HEAD requests (used by browsers to check if resources exist)"""
        # Check if this is an API request
        if self.path.startswith('/api/'):
            # Create an instance of the API handler and process the request
            api_instance = handler(self.request, self.client_address, self.server)
            api_instance.path = self.path
            api_instance.headers = self.headers
            api_instance.do_HEAD()
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
            # Create an instance of the API handler and process the request
            api_instance = handler(self.request, self.client_address, self.server)
            api_instance.path = self.path
            api_instance.headers = self.headers
            api_instance.do_GET()
            return
            
        # Try to serve static file
        build_dir = os.path.join(os.getcwd(), "my-voice-assistant/build")
        file_path = self._get_file_path(build_dir)
        
        # Special handling for root path - serve index.html
        if file_path.endswith('/'):
            file_path = os.path.join(build_dir, 'index.html')
            
        # If path doesn't exist and it's not an API call, serve index.html for SPA routing
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
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
        """Handle POST requests - pass to API handler"""
        # Create an instance of the API handler and process the request
        api_instance = handler(self.request, self.client_address, self.server)
        api_instance.path = self.path
        api_instance.headers = self.headers
        api_instance.rfile = self.rfile
        api_instance.do_POST()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests - pass to API handler"""
        # Create an instance of the API handler and process the request
        api_instance = handler(self.request, self.client_address, self.server)
        api_instance.path = self.path
        api_instance.headers = self.headers
        api_instance.do_OPTIONS()
    
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
            # Default to binary
            return 'application/octet-stream'
        return content_type

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
        
        # Start server with our custom handler that can serve static files
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
EOSPY

# Start the server
python server.py
EOF

chmod +x start.sh

echo "==> Build completed!" 