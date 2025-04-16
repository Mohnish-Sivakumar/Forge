from flask import Flask, request, jsonify, Response, stream_with_context, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
import logging
import os
import json
import io

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import Kokoro only if it's available
try:
    import kokoro
    logger.info(f"Successfully imported Kokoro v{kokoro.__version__}")
    kokoro_available = True
    pipeline = None  # Initialize as None, create only when needed
except ImportError as e:
    kokoro_available = False
    logger.warning(f"Kokoro TTS not available: {e}")
    logger.warning("Voice endpoints will return text-only responses")

# Check if we're serving static files too (combined deployment)
SERVE_STATIC = os.environ.get("SERVE_STATIC", "False").lower() in ("true", "1", "t")
static_folder = "../my-voice-assistant/build" if SERVE_STATIC else None

app = Flask(__name__, static_folder=static_folder)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize Gemini API with API key from environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDrxMRoQ-Knm7gM_6YNHAiPhXoC6HN09S4")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def init_kokoro():
    """Initialize Kokoro TTS pipeline if not already done"""
    global pipeline, kokoro_available
    if kokoro_available and pipeline is None:
        try:
            # For Kokoro 0.9.4, we need to import and use differently
            from kokoro import TTSEngine
            
            # Initialize the engine
            pipeline = TTSEngine()
            logger.info("Successfully initialized Kokoro TTS Engine")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Kokoro: {e}")
            kokoro_available = False
            return False
    return kokoro_available

def generate_speech(text):
    """Generate speech from text using Kokoro if available"""
    if not init_kokoro():
        logger.warning("Kokoro not initialized, returning None")
        return None
    
    try:
        import soundfile as sf
        import numpy as np
        
        logger.info(f"Generating speech for text: {text[:30]}...")
        
        # Generate audio using Kokoro 0.9.4 API
        audio = pipeline.tts(text)
        
        if audio is None or len(audio) == 0:
            logger.warning("No audio generated")
            return None
            
        # Convert to WAV format in memory
        buffer = io.BytesIO()
        sf.write(buffer, audio, 24000, format='WAV')
        buffer.seek(0)
        
        logger.info(f"Successfully generated audio of size: {len(buffer.getvalue())} bytes")
        return buffer.read()
    except Exception as e:
        logger.error(f"Error generating speech: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({"status": "healthy"})

@app.route('/')
def home():
    if SERVE_STATIC:
        return send_from_directory(app.static_folder, 'index.html')
    return jsonify({"message": "Welcome to the Interview AI API!"})

# Serve static files if SERVE_STATIC is enabled
@app.route('/<path:path>')
def serve_static(path):
    if SERVE_STATIC:
        if path.startswith('api/'):
            # Don't try to serve API calls as static files
            return jsonify({"error": "Not found"}), 404
        elif os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            # Return index.html for client-side routing
            return send_from_directory(app.static_folder, 'index.html')
    return jsonify({"error": "Not found"}), 404

@app.route('/api/text', methods=['POST', 'OPTIONS'])
def text_response():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        user_input = data.get('text', '')
        
        if not user_input:
            return jsonify({"status": "error", "message": "No input text provided"}), 400
            
        prompt = f"""
        Respond to: {user_input}
        Important: Provide your response as a continuous paragraph without line breaks or bullet points.
        Keep punctuation minimal, using mostly commas and periods. Your response must be concise and strictly limited to a maximum of 30 words. Remember you're an 
        interviewer. Ask the questions, and provide feedback after hearing the response from the user.
        """
        
        response_text = model.generate_content(prompt).text
        response_text = ' '.join(response_text.split())
        
        logger.info(f"Generated response: {response_text}")
        
        return jsonify({"status": "success", "response": response_text})
    
    except Exception as e:
        logger.error(f"Error in text response: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/voice', methods=['POST', 'OPTIONS'])
def voice_response():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        user_input = data.get('text', '')
        
        if not user_input:
            return jsonify({"status": "error", "message": "No input text provided"}), 400
            
        prompt = f"""
        Respond to: {user_input}
        Important: Provide your response as a continuous paragraph without line breaks or bullet points.
        Keep punctuation minimal, using mostly commas and periods. Your response must be concise and strictly limited to a maximum of 30 words. Remember you're an 
        interviewer. Ask the questions, and provide feedback after hearing the response from the user.
        """
        
        response_text = model.generate_content(prompt).text
        response_text = ' '.join(response_text.split())
        
        logger.info(f"Generated response: {response_text}")
        
        # Check if Kokoro is available
        if kokoro_available:
            logger.info("Kokoro is available, generating audio")
            audio_data = generate_speech(response_text)
            if audio_data:
                # Return audio with text in header
                logger.info("Audio generated successfully, returning response")
                response = Response(audio_data, mimetype='audio/wav')
                response.headers['X-Response-Text'] = response_text
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Expose-Headers'] = 'X-Response-Text'
                return response
            else:
                logger.warning("Audio generation failed, falling back to text")
        else:
            logger.warning("Kokoro not available, returning text response")
        
        # Fallback to text response if TTS fails or isn't available
        return jsonify({"status": "success", "response": response_text})
    
    except Exception as e:
        logger.error(f"Error in voice response: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        username = data.get('username', '')
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({"status": "error", "message": "Username and password are required"}), 400
            
        # For testing purposes only - in a real app, use proper auth
        if username == "test" and password == "password":
            return jsonify({
                "status": "success",
                "message": "Login successful",
                "token": "test-token-12345"
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Invalid credentials"
            }), 401
    
    except Exception as e:
        logger.error(f"Error in login: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def _build_cors_preflight_response():
    response = jsonify({})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    response.headers.add("Access-Control-Expose-Headers", "X-Response-Text")
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port) 