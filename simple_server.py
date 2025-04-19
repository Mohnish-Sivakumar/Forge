import os
import sys
import json
import logging
from flask import Flask, request, jsonify, send_from_directory, send_file, Response
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the test function from api/index.py to handle API requests
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from api.index import test, generate_response
    logger.info("Successfully imported API handlers")
except ImportError as e:
    logger.error(f"Failed to import API handlers: {e}")
    
# Create Flask app
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

# Find static directory - check multiple locations to be safe
STATIC_DIR = None
possible_dirs = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "my-voice-assistant", "build"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "static"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "api", "static"),
]

for dir_path in possible_dirs:
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        STATIC_DIR = dir_path
        logger.info(f"Using static directory: {STATIC_DIR}")
        break

if not STATIC_DIR:
    logger.warning("No static directory found, creating a minimal one")
    STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_static")
    os.makedirs(STATIC_DIR, exist_ok=True)
    
    # Create a minimal index.html
    with open(os.path.join(STATIC_DIR, "index.html"), "w") as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Voice Assistant API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                h1 { color: #333; }
                .container { max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Voice Assistant API</h1>
                <p>The API is running, but no static files were found.</p>
            </div>
        </body>
        </html>
        """)

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "static_dir": STATIC_DIR,
        "message": "Simple server is running"
    })

# API endpoints
@app.route('/api/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def api_route(path):
    try:
        # For OPTIONS requests (CORS)
        if request.method == 'OPTIONS':
            response = Response()
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
            return response
            
        # Create an event dict that matches what the test function expects
        event = {
            'path': f'/api/{path}',
            'httpMethod': request.method,
            'headers': {k.lower(): v for k, v in request.headers.items()},
            'queryStringParameters': request.args.to_dict(),
        }
        
        # For POST requests, add the body
        if request.method == 'POST':
            try:
                if request.is_json:
                    event['body'] = json.dumps(request.get_json())
                else:
                    event['body'] = request.get_data(as_text=True)
            except Exception as e:
                logger.error(f"Error parsing request body: {e}")
                event['body'] = '{}'
        
        # Call the handler function
        logger.info(f"Handling API request: {request.method} /api/{path}")
        result = test(event, {})
        
        # Extract status code, headers and body
        status_code = result.get('statusCode', 200)
        headers = result.get('headers', {})
        body = result.get('body', '{}')
        
        # Create response
        response = Response(body)
        response.status_code = status_code
        
        # Add headers
        for key, value in headers.items():
            response.headers[key] = value
            
        # Add CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        
        return response
    except Exception as e:
        logger.exception(f"Error handling API request: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500

# Serve static files and handle API root endpoint
@app.route('/api', methods=['GET', 'POST', 'OPTIONS'])
def api_root():
    return api_route('')

# Specific route for favicon.ico
@app.route('/favicon.ico')
def favicon():
    try:
        # Try multiple locations for favicon
        for location in [
            os.path.join(STATIC_DIR, 'favicon.ico'),
            os.path.join(STATIC_DIR, 'static', 'favicon.ico')
        ]:
            if os.path.exists(location):
                return send_file(location, mimetype='image/x-icon')
    except Exception as e:
        logger.error(f"Error serving favicon: {e}")
    
    # Return a 204 No Content if favicon not found
    return '', 204

# Special route for static files
@app.route('/static/<path:path>')
def serve_static_files(path):
    # Look in multiple possible static directories
    possible_static_dirs = [
        os.path.join(STATIC_DIR, 'static'),
        STATIC_DIR
    ]
    
    for static_dir in possible_static_dirs:
        try:
            if os.path.exists(os.path.join(static_dir, path)):
                logger.info(f"Serving static file from {static_dir}: {path}")
                return send_from_directory(static_dir, path)
        except Exception as e:
            logger.error(f"Error serving static file {path} from {static_dir}: {e}")
    
    logger.warning(f"Static file not found: {path}")
    return 'File not found', 404

# Serve index.html for root and all other non-API routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    # Special case for static files that might not start with /static
    if path.startswith(('js/', 'css/', 'media/')):
        for prefix in ('js/', 'css/', 'media/'):
            if path.startswith(prefix):
                # Try to find in the /static directory first
                try:
                    static_path = os.path.join(STATIC_DIR, 'static', path)
                    if os.path.exists(static_path):
                        return send_file(static_path)
                except Exception as e:
                    logger.error(f"Error serving {path}: {e}")
    
    # If path is empty or doesn't exist, serve index.html
    try:
        # First try the path directly
        target_path = os.path.join(STATIC_DIR, path)
        if os.path.exists(target_path) and not os.path.isdir(target_path):
            logger.info(f"Serving static file: {path}")
            return send_file(target_path)
    except Exception as e:
        logger.error(f"Error serving {path}: {e}")
    
    # If path doesn't exist or is a directory, serve index.html
    try:
        logger.info(f"Serving index.html for path: {path}")
        return send_file(os.path.join(STATIC_DIR, 'index.html'))
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        return f"Error serving the application: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting simple server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False) 