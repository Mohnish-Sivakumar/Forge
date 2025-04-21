from flask import Flask, request, jsonify, Response, send_from_directory, stream_with_context
from flask_cors import CORS
import google.generativeai as genai
import logging
import os
import io
import json
import base64
import requests
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Check if we're serving static files too (combined deployment)
SERVE_STATIC = os.environ.get("SERVE_STATIC", "False").lower() in ("true", "1", "t")
static_folder = os.path.abspath("../my-voice-assistant/build") if SERVE_STATIC else None
static_url_path = '' if SERVE_STATIC else None

app = Flask(__name__, static_folder=static_folder, static_url_path=static_url_path)

# Configure CORS to allow requests from development server
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Setup debug logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# Initialize Gemini API with API key from environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDrxMRoQ-Knm7gM_6YNHAiPhXoC6HN09S4")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize Speechify TTS API key
SPEECHIFY_API_KEY = os.environ.get("SPEECHIFY_API_KEY", "fwsjj7SjBEmJ9C058GN5NLEEIfwOga3tYKkftbo_TQE=")

# Configure available voices for Speechify
AVAILABLE_VOICES = {
    'default': 'belinda',  # Default Speechify voice
    'female1': 'aria',   # Female voice 1
    'female2': 'jane',   # Female voice 2
    'male1': 'matthew',  # Male voice 1
    'male2': 'ryan',     # Male voice 2
    'british': 'tom',    # British voice
    'australian': 'joseph'  # Another voice option
}

def text_to_speech(text, voice='default'):
    """Convert text to speech using Speechify API"""
    app.logger.info(f"Generating voice using Speechify API with voice: {voice}")
    
    # Select voice from available options
    voice_id = AVAILABLE_VOICES.get(voice, AVAILABLE_VOICES['default'])
    app.logger.info(f"Selected Speechify voice ID: {voice_id}")
    
    try:
        # Process text to clean it for better speech generation
        processed_text = text.replace('\n', ' ').strip()
        
        # Speechify API endpoint
        url = "https://api.sws.speechify.com/v1/audio/speech"
        
        # Request headers with API key
        headers = {
            "Authorization": f"Bearer {SPEECHIFY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Request body
        payload = {
            "input": processed_text,
            "voice_id": voice_id
        }
        
        # Make the API request
        app.logger.info(f"Calling Speechify API with text length: {len(processed_text)}")
        response = requests.post(url, headers=headers, json=payload)
        
        # Check if the request was successful
        if response.status_code != 200:
            app.logger.error(f"Speechify API error: {response.status_code} - {response.text}")
            return None
        
        # Get the response JSON
        response_data = response.json()
        
        # Check if we have the audio_url in the response
        if 'audio_url' in response_data:
            # Download the audio from the URL
            audio_response = requests.get(response_data['audio_url'])
            if audio_response.status_code == 200:
                # Return the audio data
                app.logger.info(f"Successfully generated audio with Speechify, size: {len(audio_response.content)} bytes")
                return audio_response.content
            else:
                app.logger.error(f"Failed to download audio from URL: {response_data['audio_url']}")
                return None
        else:
            app.logger.error(f"No audio_url in Speechify API response: {response_data}")
            return None
    
    except Exception as e:
        app.logger.error(f"Error generating speech with Speechify: {e}")
        return None

def chunk_text(text, max_length=300):
    """Split text into smaller chunks, trying to break at sentence boundaries."""
    # If text is already small enough, return it as is
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    # Common sentence ending punctuation
    sentence_enders = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
    
    # Try to split by sentences first
    current_chunk = ''
    sentences = []
    
    # First, break text into sentences
    last_end = 0
    for i in range(1, len(text)):
        if any(text[i-1:i+1] == ender for ender in sentence_enders):
            sentences.append(text[last_end:i+1])
            last_end = i+1
    
    # Add any remaining text as the last sentence
    if last_end < len(text):
        sentences.append(text[last_end:])
    
    # Now group sentences into chunks of appropriate length
    current_chunk = ''
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence
        else:
            # If the current chunk is not empty, add it to chunks
            if current_chunk:
                chunks.append(current_chunk)
            
            # If the sentence itself is longer than max_length,
            # split it by words (less ideal but necessary)
            if len(sentence) > max_length:
                words = sentence.split(' ')
                current_chunk = ''
                for word in words:
                    if len(current_chunk) + len(word) + 1 <= max_length:  # +1 for space
                        if current_chunk:
                            current_chunk += ' ' + word
                        else:
                            current_chunk = word
                    else:
                        chunks.append(current_chunk)
                        current_chunk = word
            else:
                current_chunk = sentence
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

@app.route('/health')
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})

@app.route('/api/test', methods=['GET', 'POST', 'OPTIONS'])
def test_endpoint():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
        
    # Simple test endpoint to check if API is working
    return jsonify({
        "status": "ok", 
        "message": "API is working", 
        "method": request.method,
        "timestamp": str(datetime.now())
    })

@app.route('/api/debug', methods=['GET', 'OPTIONS'])
def debug():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
        
    # Get system info
    debug_info = {
        "api_version": "1.0.0",
        "python_version": sys.version,
        "flask_version": flask.__version__,
        "env": os.environ.get("FLASK_ENV", "not set"),
        "available_voices": list(AVAILABLE_VOICES.keys()),
        "tts_provider": "Speechify",
        "gemini_model": "gemini-1.5-flash"
    }
    
    return jsonify(debug_info)

@app.route('/')
def home():
    """Serve static files if SERVE_STATIC is enabled, otherwise redirect to /api"""
    if SERVE_STATIC:
        return send_from_directory(app.static_folder, 'index.html')
    else:
        return jsonify({"status": "ok", "message": "API is running"})

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files if SERVE_STATIC is enabled"""
    if SERVE_STATIC:
        # Check if path exists in static folder
        static_path = os.path.join(app.static_folder, path)
        if os.path.exists(static_path) and os.path.isfile(static_path):
            return send_from_directory(app.static_folder, path)
        else:
            # Return index.html for client-side routing
            return send_from_directory(app.static_folder, 'index.html')
    else:
        return jsonify({"status": "error", "message": "Not found"}), 404

# API endpoint for text processing
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
        
        # Check if this is the welcome message
        if "Welcome to interview AI" in user_input:
            # Return the welcome message directly without sending to AI
            return jsonify({"status": "success", "response": user_input})
            
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

# Voice API endpoint with Speechify
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
        voice_option = data.get('voice', 'default')  # Default to standard English voice
        format_preference = data.get('format', '').lower()  # Check if client prefers a specific format
        
        if not user_input:
            return jsonify({"status": "error", "message": "No input text provided"}), 400
        
        # Check if this is the welcome message
        if "Welcome to interview AI" in user_input:
            # Return the welcome message directly without sending to AI
            audio_data = text_to_speech(user_input, voice=voice_option)
            
            if audio_data:
                # Return base64 encoded audio
                encoded_audio = base64.b64encode(audio_data).decode('utf-8')
                return jsonify({
                    "status": "success",
                    "response": user_input,
                    "audio": encoded_audio,
                    "format": "mp3"  # Speechify returns MP3
                })
            else:
                # Fallback to text only
                return jsonify({
                    "status": "partial_success",
                    "message": "Text generated successfully, but audio generation failed. Using browser TTS fallback.",
                    "response": user_input,
                    "fallback": True
                })
            
        # Generate response with Gemini
        prompt = f"""
        Respond to: {user_input}
        Important: Provide your response as a continuous paragraph without line breaks or bullet points.
        Keep punctuation minimal, using mostly commas and periods. Your response must be concise and strictly limited to a maximum of 50 words. Remember you're an 
        interviewer. Ask the questions, and provide feedback after hearing the response from the user.
        """
        
        response_text = model.generate_content(prompt).text
        response_text = ' '.join(response_text.split())
        
        logging.info(f"Generated voice response: {response_text}")
        
        # Get audio from Speechify
        audio_data = text_to_speech(response_text, voice=voice_option)
        
        if audio_data:
            # Return base64 encoded audio
            encoded_audio = base64.b64encode(audio_data).decode('utf-8')
            return jsonify({
                "status": "success",
                "response": response_text,
                "audio": encoded_audio,
                "format": "mp3"  # Speechify returns MP3
            })
        else:
            # Fallback to text only
            return jsonify({
                "status": "partial_success",
                "message": "Text generated successfully, but audio generation failed. Using browser TTS fallback.",
                "response": response_text,
                "fallback": True
            })
            
    except Exception as e:
        logging.error(f"Error in voice response: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e),
            "response": "Sorry, I couldn't generate a voice response."
        }), 500

# API endpoint for login
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
    # Get the Origin from the request headers
    origin = request.headers.get('Origin', '*')
    
    # Create response with CORS headers
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port) 