import os
import sys
import logging
from flask import Flask, request, jsonify, send_from_directory, Response, redirect

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Determine the static folder path
static_folder = None
if os.path.exists(os.path.join("api", "static")):
    static_folder = os.path.join("api", "static")
elif os.path.exists(os.path.join("backend", "static")):
    static_folder = os.path.join("backend", "static")
elif os.path.exists(os.path.join("my-voice-assistant", "build")):
    static_folder = os.path.join("my-voice-assistant", "build")

# Log the static folder
logger.info(f"Using static folder: {static_folder}")

# Handle API requests - use either API or backend implementation
api_handler = None
try:
    logger.info("Trying to import API handler from api/index.py...")
    sys.path.insert(0, os.path.abspath("api"))
    from api.index import handler as ApiHandler
    api_handler = "index"
    logger.info("Successfully imported handler from api/index.py")
except ImportError as e:
    logger.warning(f"Could not import from api/index.py: {e}")
    try:
        logger.info("Trying to import from backend/app.py...")
        sys.path.insert(0, os.path.abspath("backend"))
        import backend.app as backend_module
        api_handler = "backend"
        logger.info("Successfully imported backend.app")
    except ImportError as e:
        logger.error(f"Could not import backend module either: {e}")
        logger.error("No API handler available")

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "python_version": sys.version,
        "static_folder": static_folder,
        "api_handler": api_handler
    })

# Redirect API requests to the API handler
@app.route('/api/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def api_route(path):
    # This is just a fallback; actual API requests should be handled by api/handler.py
    return jsonify({
        "status": "error",
        "message": "API requests should be handled by the main handler",
        "path": path
    })

# Base API route
@app.route('/api', methods=['GET', 'POST', 'OPTIONS'])
def api_base_route():
    return api_route("")

# Serve static files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    if not path or path == '':
        path = 'index.html'
    
    logger.info(f"Serving static file: {path}")
    
    if static_folder:
        # Special handling for static directory (CSS, JS, etc.)
        if path.startswith('static/'):
            # If the path starts with 'static/', serve from the static subfolder 
            return send_from_directory(static_folder, path)
        else:
            try:
                # Try to serve directly from the static folder
                return send_from_directory(static_folder, path)
            except:
                # If not found, try serving from the "static" subdirectory
                # This handles requests like /favicon.ico that might be in either location
                try:
                    return send_from_directory(os.path.join(static_folder, 'static'), path)
                except Exception as e:
                    logger.error(f"Error serving static file {path}: {e}")
                    return f"File not found: {path}", 404
    else:
        logger.error(f"No static folder available to serve {path}")
        return f"Static files not available. Path requested: {path}", 404

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port) 