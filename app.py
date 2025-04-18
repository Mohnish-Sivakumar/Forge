import os
import sys
import logging
from flask import Flask, request, jsonify, send_from_directory

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Determine the static folder path
static_folder = None
if os.path.exists(os.path.join("backend", "static")):
    static_folder = os.path.join("backend", "static")
elif os.path.exists(os.path.join("api", "static")):
    static_folder = os.path.join("api", "static")
elif os.path.exists(os.path.join("my-voice-assistant", "build")):
    static_folder = os.path.join("my-voice-assistant", "build")

# Log the static folder
logger.info(f"Using static folder: {static_folder}")

# Import the API handler
try:
    # First, try to import from backend
    logger.info("Trying to import from backend...")
    sys.path.insert(0, "backend")
    from backend.app import app as backend_app
    
    # Use all routes from backend_app
    logger.info("Successfully imported backend.app")
    
    # Register backend routes
    for rule in backend_app.url_map.iter_rules():
        logger.info(f"Registering route from backend: {rule.rule}")
        app.register_blueprint(backend_app)
    
except ImportError as e:
    logger.info(f"Could not import from backend: {e}")
    try:
        # Try to import from api
        logger.info("Trying to import from api...")
        sys.path.insert(0, "api")
        from api.index import handler
        
        # Create a wrapper for the api handler
        @app.route('/api/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
        def api_route(path):
            logger.info(f"API route: /{path}")
            # Create a handler instance
            h = handler()
            # Handle the request
            return h(request.environ, lambda s, h: (s, h, []))
        
        logger.info("Successfully imported api.index")
    except ImportError as e:
        logger.error(f"Could not import from api either: {e}")
        logger.error("No API handler available")

# Serve static files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    if not path or path == '':
        path = 'index.html'
    
    logger.info(f"Serving static file: {path}")
    
    if static_folder:
        return send_from_directory(static_folder, path)
    else:
        return f"Static files not available. Path requested: {path}"

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "python_version": sys.version,
        "static_folder": static_folder
    })

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port) 