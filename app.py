import os
import sys
import logging
from flask import Flask, request, jsonify, send_from_directory, Response

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

# API route handler
@app.route('/api/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def api_route(path):
    """Handle API requests by forwarding to the appropriate handler"""
    if api_handler == "index":
        logger.info(f"Handling API request to /api/{path} using api/index.py")
        try:
            # Create a request handler instance
            from api.index import handler
            h = handler()
            
            # Set the path and method
            h.path = f"/api/{path}"
            h.command = request.method
            
            # Prepare the request environment
            def start_response(status, headers):
                status_code = int(status.split()[0])
                resp = Response(status=status_code)
                for key, value in headers:
                    resp.headers[key] = value
                return resp
            
            # Process the request
            if request.method == 'OPTIONS':
                h.do_OPTIONS()
                return Response(status=200)
            elif request.method == 'GET':
                h.do_GET()
                return Response(status=200)
            elif request.method == 'POST':
                # Provide the POST data
                h.headers = {key: value for key, value in request.headers.items()}
                h.rfile = request.stream
                h.do_POST()
                return Response(status=200)
        except Exception as e:
            logger.error(f"Error handling API request: {e}")
            return jsonify({"error": str(e)}), 500
    
    elif api_handler == "backend":
        logger.info(f"Forwarding API request to backend.app: /api/{path}")
        try:
            # Use the backend module's routes
            return backend_module.app.handle_request(request)
        except Exception as e:
            logger.error(f"Error forwarding to backend: {e}")
            return jsonify({"error": str(e)}), 500
    
    else:
        logger.error(f"No API handler available for /api/{path}")
        return jsonify({"error": "API handler not available"}), 501

# Base API route
@app.route('/api', methods=['GET', 'POST', 'OPTIONS'])
def api_base_route():
    """Handle base API requests"""
    return api_route("")

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "python_version": sys.version,
        "static_folder": static_folder,
        "api_handler": api_handler
    })

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

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port) 