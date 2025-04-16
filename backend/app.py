from flask import Flask, request, jsonify, Response, stream_with_context, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
import logging
import os
import json
import io
import soundfile as sf
from kokoro import KPipeline

# Check if we're serving static files too (combined deployment)
SERVE_STATIC = os.environ.get("SERVE_STATIC", "False").lower() in ("true", "1", "t")
static_folder = "../my-voice-assistant/build" if SERVE_STATIC else None

app = Flask(__name__, static_folder=static_folder)
CORS(app, resources={r"/*": {"origins": "*"}})
logging.basicConfig(level=logging.INFO)

# Initialize Gemini API with API key from environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDrxMRoQ-Knm7gM_6YNHAiPhXoC6HN09S4")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize Kokoro TTS
try:
    pipeline = KPipeline(lang_code='a')  # Only supports basic initialization
    kokoro_available = True
    logging.info("Kokoro TTS initialized successfully")
except Exception as e:
    kokoro_available = False
    logging.error(f"Failed to initialize Kokoro TTS: {e}")

def process_text_chunk(text):
    """Process text through Kokoro TTS and return audio data"""
    try:
        generator = pipeline(text, voice='af_heart')
        for _, _, audio in generator:
            buffer = io.BytesIO()
            sf.write(buffer, audio, 24000, format='WAV')
            buffer.seek(0)
            audio_data = buffer.read()
            logging.debug(f"Audio data size: {len(audio_data)} bytes")
            yield audio_data
    except Exception as e:
        logging.error(f"Error processing chunk: {e}")

def generate_speech_chunks(text):
    """Split text into sentences and generate audio for each one"""
    chunks = [c.strip() + '.' for c in text.split('.') if c.strip()]
    for chunk in chunks:
        if chunk:
            for audio in process_text_chunk(chunk):
                if audio:
                    logging.debug("Yielding audio chunk")
                    yield audio

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
        
        logging.info(f"Generated response: {response_text}")
        
        return jsonify({"status": "success", "response": response_text})
    
    except Exception as e:
        logging.error(f"Error in text response: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/voice', methods=['POST', 'OPTIONS'])
def voice_response():
    """Generate voice response using Kokoro TTS"""
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
        
        # Check if Kokoro is available
        if not kokoro_available:
            return jsonify({
                "status": "error", 
                "message": "Voice synthesis is not available. Using text-only response.",
                "response": "Voice synthesis unavailable. Please use text API."
            }), 503
            
        prompt = f"""
        Respond to: {user_input}
        Important: Provide your response as a continuous paragraph without line breaks or bullet points.
        Keep punctuation minimal, using mostly commas and periods. Your response must be concise and strictly limited to a maximum of 30 words. Remember you're an 
        interviewer. Ask the questions, and provide feedback after hearing the response from the user.
        """
        
        response_text = model.generate_content(prompt).text
        response_text = ' '.join(response_text.split())
        
        logging.info(f"Generated voice response: {response_text}")
        
        # Set headers to include the text response
        headers = {
            'Content-Type': 'audio/wav',
            'X-Response-Text': response_text
        }
        
        return Response(
            stream_with_context(generate_speech_chunks(response_text)),
            mimetype='audio/wav',
            headers=headers
        )
    
    except Exception as e:
        logging.error(f"Error in voice response: {e}")
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
        logging.error(f"Error in login: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def _build_cors_preflight_response():
    response = jsonify({})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port) 