import os
import json
import logging
import sys
import glob
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('app')

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Memory optimization flag
LOW_MEMORY_MODE = os.environ.get('LOW_MEMORY_MODE', 'true').lower() == 'true'
SERVE_STATIC = os.environ.get('SERVE_STATIC', 'true').lower() == 'true'

# Primary static folder path
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'my-voice-assistant', 'build')

# Alternative paths that might be used on Render
ALTERNATIVE_PATHS = [
    os.path.join(os.getcwd(), 'my-voice-assistant', 'build'),
    os.path.join(os.getcwd(), 'build_backup'),
    '/opt/render/project/src/my-voice-assistant/build',
    '/app/my-voice-assistant/build'
]

# Use the first existing path
for path in ALTERNATIVE_PATHS:
    if os.path.exists(path):
        STATIC_FOLDER = path
        logger.info(f"Using static folder: {STATIC_FOLDER}")
        break

logger.info(f"Final static folder: {STATIC_FOLDER}")
logger.info(f"Static folder exists: {os.path.exists(STATIC_FOLDER)}")
if os.path.exists(STATIC_FOLDER):
    logger.info(f"Static folder contents: {os.listdir(STATIC_FOLDER)}")

# Lazy loading of dependencies
google_ai = None
kokoro = None
torch = None
numpy = None

# Load Gemini API when needed
def load_gemini():
    global google_ai
    if google_ai is None:
        try:
            import google.generativeai as genai
            api_key = os.environ.get("GOOGLE_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
            if not api_key:
                logging.error("API key environment variable not set")
                return False
            
            genai.configure(api_key=api_key)
            google_ai = genai
            logging.info("Google Generative AI loaded successfully")
            return True
        except ImportError as e:
            logging.error(f"Failed to import Google Generative AI: {e}")
            return False
    return True

# Load TTS dependencies only when needed
def load_tts_deps():
    global kokoro, torch, numpy
    if LOW_MEMORY_MODE:
        return False
        
    if kokoro is None:
        try:
            import kokoro as k
            import torch as t
            import numpy as np
            kokoro = k
            torch = t
            numpy = np
            logging.info("TTS dependencies loaded successfully")
            return True
        except ImportError as e:
            logging.error(f"Failed to import TTS dependencies: {e}")
            return False
    return True

# Text-to-speech function (with memory optimization)
def text_to_speech(text, voice='default'):
    """Convert text to speech using Kokoro or return error if unavailable"""
    if not text:
        return None, {"error": "No text provided"}
        
    if LOW_MEMORY_MODE:
        logging.info("TTS skipped due to LOW_MEMORY_MODE=true")
        return None, {"message": "Voice generation is disabled in low-memory mode"}
    
    # Only try to load TTS dependencies if needed
    if not load_tts_deps():
        return None, {"error": "TTS dependencies not available"}
    
    # Simple implementation that just returns a message in this version
    return None, {"message": "Voice synthesis is not available in this deployment"}

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "config": {
            "low_memory_mode": LOW_MEMORY_MODE,
            "serve_static": SERVE_STATIC,
            "gemini_api_available": load_gemini()
        }
    })

@app.route('/api/test', methods=['GET', 'POST', 'OPTIONS'])
def test_endpoint():
    """Test endpoint that returns a simple response"""
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    if request.method == 'GET':
        return jsonify({
            "message": "API is working",
            "endpoints": ["/api/text", "/api/voice", "/api/login"],
            "status": "ok"
        })
    
    # Handle POST
    try:
        data = request.get_json() or {}
        message = data.get('text', 'No message provided')
        
        return jsonify({
            "message": "Request received",
            "request_data": message,
            "status": "ok"
        })
    except Exception as e:
        logging.error(f"Error in test endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/debug', methods=['GET', 'OPTIONS'])
def debug():
    """Debug endpoint that returns system status"""
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    # Prepare response with system info
    info = {
        "status": "ok",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "memory_mode": "low" if LOW_MEMORY_MODE else "normal",
        "serve_static": SERVE_STATIC,
        "gemini_api_available": load_gemini(),
        "voice_synthesis_available": not LOW_MEMORY_MODE,
        "endpoints": ["/api/text", "/api/voice", "/api/login"],
        "environment": os.environ.get("FLASK_ENV", "development")
    }
    
    # Add static files info
    static_info = {
        "static_folder": STATIC_FOLDER,
        "static_folder_exists": os.path.exists(STATIC_FOLDER),
        "index_html_exists": os.path.exists(os.path.join(STATIC_FOLDER, 'index.html')),
        "static_dir_exists": os.path.exists(os.path.join(STATIC_FOLDER, 'static')),
        "current_directory": os.getcwd(),
    }
    info["static_files"] = static_info
    
    # Add memory info if possible
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        info["memory"] = {
            "rss_mb": memory_info.rss / (1024 * 1024),
            "vms_mb": memory_info.vms / (1024 * 1024)
        }
    except ImportError:
        pass
    
    return jsonify(info)

@app.route('/api/files', methods=['GET'])
def list_files():
    """List files in the build directory to help with debugging"""
    if not SERVE_STATIC:
        return jsonify({"error": "Static file serving is disabled"}), 404
    
    file_list = []
    css_files = []
    js_files = []
    
    # Check if build directory exists
    if os.path.exists(STATIC_FOLDER):
        # List main directory
        file_list = os.listdir(STATIC_FOLDER)
        
        # List CSS files
        css_path = os.path.join(STATIC_FOLDER, 'static', 'css')
        if os.path.exists(css_path):
            css_files = os.listdir(css_path)
            
        # List JS files
        js_path = os.path.join(STATIC_FOLDER, 'static', 'js')
        if os.path.exists(js_path):
            js_files = os.listdir(js_path)
    
    return jsonify({
        "build_dir": STATIC_FOLDER,
        "exists": os.path.exists(STATIC_FOLDER),
        "files": file_list,
        "css_files": css_files,
        "js_files": js_files,
        "cwd": os.getcwd()
    })

@app.route('/')
def home():
    """Serve the main page or API info"""
    if SERVE_STATIC and os.path.exists(os.path.join(STATIC_FOLDER, 'index.html')):
        return send_from_directory(STATIC_FOLDER, 'index.html')
    
    return jsonify({
        "name": "Interview AI API",
        "version": "1.0.0",
        "endpoints": ["/api/text", "/api/voice", "/api/login", "/api/debug"],
        "docs": "/api/debug"
    })

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from the React build directory"""
    if not SERVE_STATIC:
        return jsonify({"error": "Static file serving is disabled"}), 404
    
    logger.info(f"Requested path: {path}")
    
    # Special case for static files (CSS, JS, media)
    if path.startswith('static/'):
        file_path = os.path.join(STATIC_FOLDER, path)
        logger.info(f"Checking static file at: {file_path}")
        if os.path.exists(file_path):
            logger.info(f"Found static file at: {file_path}")
            return send_from_directory(STATIC_FOLDER, path)
        logger.warning(f"Static file not found at: {file_path}")
        return '', 404

    # Handle common assets
    if path in ['favicon.ico', 'manifest.json', 'logo192.png', 'logo512.png', 'robots.txt']:
        file_path = os.path.join(STATIC_FOLDER, path)
        logger.info(f"Checking asset at: {file_path}")
        if os.path.exists(file_path):
            logger.info(f"Found asset at: {file_path}")
            return send_from_directory(STATIC_FOLDER, path)
        logger.warning(f"Asset not found at: {file_path}")
    
    # Return index.html for all other routes to support React Router
    index_path = os.path.join(STATIC_FOLDER, 'index.html')
    logger.info(f"Returning index.html from: {index_path}")
    if os.path.exists(index_path):
        return send_from_directory(STATIC_FOLDER, 'index.html')
    
    # If index.html doesn't exist, return an error message
    logger.error(f"index.html not found at: {index_path}")
    return f"Static files not found. STATIC_FOLDER={STATIC_FOLDER}, path requested: {path}", 404

# Add a specific route for static directory
@app.route('/static/<path:filename>')
def serve_static_dir(filename):
    """
    Specific handler for /static/ URLs
    This is critical for serving React's JS and CSS files
    """
    static_dir = os.path.join(STATIC_FOLDER, 'static')
    logger.info(f"Serving static file: {filename} from {static_dir}")
    
    # Check if the file exists in static/css or static/js
    file_path = os.path.join(static_dir, filename)
    if os.path.exists(file_path):
        logger.info(f"Found file at: {file_path}")
        return send_from_directory(static_dir, filename)
    
    # If not found, try other possible locations
    if '/' in filename:
        directory, fname = filename.split('/', 1)
        dir_path = os.path.join(static_dir, directory)
        full_path = os.path.join(dir_path, fname)
        logger.info(f"Checking alternate path: {full_path}")
        if os.path.exists(full_path):
            logger.info(f"Found file at alternate path: {full_path}")
            return send_from_directory(dir_path, fname)
    
    # Check for similar files as a last resort
    if filename.endswith('.js'):
        js_dir = os.path.join(static_dir, 'js')
        if os.path.exists(js_dir):
            js_files = glob.glob(os.path.join(js_dir, '*.js'))
            if js_files:
                found_file = os.path.basename(js_files[0])
                logger.info(f"Fallback to similar JS file: {found_file}")
                return send_from_directory(js_dir, found_file)
    
    if filename.endswith('.css'):
        css_dir = os.path.join(static_dir, 'css')
        if os.path.exists(css_dir):
            css_files = glob.glob(os.path.join(css_dir, '*.css'))
            if css_files:
                found_file = os.path.basename(css_files[0])
                logger.info(f"Fallback to similar CSS file: {found_file}")
                return send_from_directory(css_dir, found_file)
    
    logger.error(f"File not found: {filename} in {static_dir}")
    return f"File not found: {filename}", 404

@app.route('/check/<path:file_path>')
def check_file(file_path):
    """
    Endpoint to check if a specific file exists and serve it
    This helps diagnose file serving issues
    """
    # First, log what we're looking for
    logger.info(f"Check requested for file: {file_path}")
    
    # Check if file exists directly in the STATIC_FOLDER
    direct_path = os.path.join(STATIC_FOLDER, file_path)
    logger.info(f"Checking direct path: {direct_path}")
    
    if os.path.isfile(direct_path):
        logger.info(f"File found at direct path: {direct_path}")
        try:
            return send_from_directory(STATIC_FOLDER, file_path)
        except Exception as e:
            logger.error(f"Error serving file: {e}")
            return jsonify({"error": str(e)}), 500
    
    # If not found directly, try alternative paths
    alternatives = []
    for alt_base in ALTERNATIVE_PATHS:
        alt_path = os.path.join(alt_base, file_path)
        exists = os.path.exists(alt_path)
        alternatives.append({
            "path": alt_path,
            "exists": exists,
            "is_file": os.path.isfile(alt_path) if exists else False
        })
        if exists and os.path.isfile(alt_path):
            logger.info(f"File found at alternative path: {alt_path}")
            try:
                return send_from_directory(os.path.dirname(alt_path), os.path.basename(alt_path))
            except Exception as e:
                logger.error(f"Error serving file from alternative path: {e}")
    
    # If file starts with static/, try to serve it from the static directory
    if file_path.startswith('static/'):
        rel_path = file_path[7:]  # Remove 'static/' prefix
        static_dir = os.path.join(STATIC_FOLDER, 'static')
        full_path = os.path.join(static_dir, rel_path)
        logger.info(f"Checking static subpath: {full_path}")
        
        if os.path.isfile(full_path):
            logger.info(f"File found at static subpath: {full_path}")
            try:
                return send_from_directory(static_dir, rel_path)
            except Exception as e:
                logger.error(f"Error serving file from static subpath: {e}")
    
    # If file not found, check for similar files
    similar_files = []
    if file_path.endswith('.js'):
        js_dir = os.path.join(STATIC_FOLDER, 'static', 'js')
        if os.path.exists(js_dir):
            similar_files = glob.glob(os.path.join(js_dir, '*.js'))
    elif file_path.endswith('.css'):
        css_dir = os.path.join(STATIC_FOLDER, 'static', 'css')
        if os.path.exists(css_dir):
            similar_files = glob.glob(os.path.join(css_dir, '*.css'))
    
    # Return diagnostic info
    return jsonify({
        "error": "File not found",
        "requested_path": file_path,
        "full_path": direct_path,
        "static_folder": STATIC_FOLDER,
        "exists": os.path.exists(direct_path),
        "is_file": os.path.isfile(direct_path),
        "parent_dir_exists": os.path.exists(os.path.dirname(direct_path)),
        "cwd": os.getcwd(),
        "alternatives": alternatives,
        "similar_files": similar_files
    }), 404

@app.route('/api/text', methods=['POST', 'OPTIONS'])
def text_response():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    # Get request data
    data = request.get_json() or {}
    text = data.get('text', '')
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    # Load Gemini API
    if not load_gemini():
        return jsonify({
            "response": "Sorry, the AI service is currently unavailable.",
            "error": "Failed to load Gemini API"
        }), 503
    
    try:
        # Generate response using Google Generative AI
        model = google_ai.GenerativeModel('gemini-pro')
        result = model.generate_content(text)
        
        # Return the response
        return jsonify({
            "response": result.text,
            "status": "success"
        })
    except Exception as e:
        logging.error(f"Error generating text response: {e}")
        return jsonify({
            "error": str(e),
            "response": "Sorry, there was an error processing your request."
        }), 500

@app.route('/api/voice', methods=['POST', 'OPTIONS'])
def voice_response():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    # Get request data
    data = request.get_json() or {}
    text = data.get('text', '')
    voice = data.get('voice', 'default')
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    # Generate AI response if requested
    if data.get('generate_text', False):
        if not load_gemini():
            return jsonify({
                "text": "Sorry, the AI service is currently unavailable.",
                "error": "Failed to load Gemini API"
            }), 503
        
        try:
            # Generate response using Google Generative AI
            model = google_ai.GenerativeModel('gemini-pro')
            result = model.generate_content(text)
            generated_text = result.text
        except Exception as e:
            logging.error(f"Error generating text response: {e}")
            return jsonify({
                "error": str(e),
                "text": "Sorry, there was an error processing your request."
            }), 500
    else:
        # Use provided text directly
        generated_text = text
    
    # Log the response for monitoring
    logging.info(f"Generated voice response: {generated_text}")
    
    # Generate audio (or get error message)
    audio_base64, error_info = text_to_speech(generated_text, voice)
    
    # Prepare response
    response_format = data.get('format', '').lower()
    
    # Handle case where TTS is disabled or fails
    if not audio_base64:
        response_data = {
            "text": generated_text,
            "status": "success",
            "message": "Text generated successfully, voice synthesis unavailable in low memory mode."
        }
        
        # Include error info if available
        if error_info:
            response_data.update(error_info)
        
        # Set appropriate headers and return
        resp = jsonify(response_data)
        resp.headers['X-Response-Text'] = generated_text[:100] + '...'
        return resp
    
    # Handle binary audio response (shouldn't normally get here in low memory mode)
    if audio_base64 and response_format != 'json':
        # Decode base64 to binary
        import base64
        audio_binary = base64.b64decode(audio_base64)
        
        response = Response(audio_binary, mimetype='audio/wav')
        response.headers['X-Response-Text'] = generated_text[:100] + '...'
        return response
    
    # Default to JSON response with base64-encoded audio
    response_data = {
        "text": generated_text,
        "status": "success"
    }
    
    if audio_base64:
        response_data["audio"] = audio_base64
        response_data["compressed"] = False
    
    resp = jsonify(response_data)
    resp.headers['X-Response-Text'] = generated_text[:100] + '...'
    return resp

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    # Get login data
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')
    
    # Simple mock login
    if username == 'test' and password == 'password':
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "user": {
                "id": "12345",
                "username": username,
                "role": "tester"
            }
        })
    
    return jsonify({
        "status": "error",
        "message": "Invalid username or password"
    }), 401

def _build_cors_preflight_response():
    # Get the Origin from the request headers
    origin = request.headers.get('Origin', '*')
    
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port) 