from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import google.generativeai as genai
import os
import logging
import json
import io
from kokoro import KPipeline
import soundfile as sf

# Initialize Flask app - this is the serverless entry point
app = Flask(__name__)
# Configure CORS properly with all necessary settings
CORS(app, resources={r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "Accept", "X-Response-Text"],
    "expose_headers": ["X-Response-Text"]
}})

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini AI
GEMINI_API_KEY = "AIzaSyDrxMRoQ-Knm7gM_6YNHAiPhXoC6HN09S4"
genai.configure(api_key=GEMINI_API_KEY)

# Lazy-loading of models and pipelines
_model = None
_pipeline = None

def get_model():
    global _model
    if _model is None:
        _model = genai.GenerativeModel('gemini-1.5-flash')
    return _model

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        try:
            _pipeline = KPipeline(lang_code='a')  # Basic initialization
        except Exception as e:
            logger.error(f"Error initializing Kokoro: {e}")
    return _pipeline

def generate_audio(text):
    """Process text to audio using Kokoro TTS"""
    tts = get_pipeline()
    if not tts:
        return None
        
    chunks = []
    try:
        for _, _, audio in tts(text, voice='af_heart'):
            buffer = io.BytesIO()
            sf.write(buffer, audio, 24000, format='WAV')
            buffer.seek(0)
            chunks.append(buffer.read())
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        return None
    
    return chunks

# Explicitly handle OPTIONS for all routes with proper CORS headers
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept, X-Response-Text')
    response.headers.add('Access-Control-Expose-Headers', 'X-Response-Text')
    return response

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "ok",
        "message": "Interview AI API is running"
    })

@app.route('/api/text', methods=['POST', 'OPTIONS'])
def text_api():
    # Handle preflight OPTIONS requests
    if request.method == 'OPTIONS':
        return handle_options('')
        
    try:
        # Get data from various possible sources
        data = None
        if request.is_json:
            data = request.json
        elif request.form:
            data = request.form
        elif request.get_data():
            try:
                data = json.loads(request.get_data())
            except:
                data = None
        
        if not data:
            data = {}
            
        user_input = data.get('text', '')
        
        if not user_input:
            return jsonify({'error': 'No input text provided'}), 400
            
        # Generate response with Gemini AI
        model = get_model()
        prompt = f"""
        Respond to: {user_input}
        Important: Provide your response as a continuous paragraph without line breaks or bullet points.
        Keep punctuation minimal, using mostly commas and periods. Your response must be concise and strictly limited to a maximum of 30 words. Remember you're an 
        interviewer. Ask the questions, and provide feedback after hearing the response from the user.
        """
        
        response_text = model.generate_content(prompt).text
        response_text = ' '.join(response_text.split())
        
        # Return JSON response
        return jsonify({'response': response_text})
    
    except Exception as e:
        logger.error(f"Error in text response: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice', methods=['POST', 'OPTIONS'])
def voice_api():
    # Handle preflight OPTIONS requests
    if request.method == 'OPTIONS':
        return handle_options('')
        
    try:
        # Get data from various possible sources
        data = None
        if request.is_json:
            data = request.json
        elif request.form:
            data = request.form
        elif request.get_data():
            try:
                data = json.loads(request.get_data())
            except:
                data = None
        
        if not data:
            data = {}
            
        user_input = data.get('text', '')
        
        if not user_input:
            return jsonify({'error': 'No input text provided'}), 400
        
        # Generate response with Gemini AI
        model = get_model()
        prompt = f"""
        Respond to: {user_input}
        Important: Provide your response as a continuous paragraph without line breaks or bullet points.
        Keep punctuation minimal, using mostly commas and periods. Your response must be concise and strictly limited to a maximum of 30 words. Remember you're an 
        interviewer. Ask the questions, and provide feedback after hearing the response from the user.
        """
        
        response_text = model.generate_content(prompt).text
        response_text = ' '.join(response_text.split())
        
        # Generate speech
        audio_chunks = generate_audio(response_text)
        
        if not audio_chunks:
            # Fall back to text if audio generation fails
            return jsonify({
                'response': response_text,
                'success': False,
                'error': 'TTS not available'
            })

        # Define a generator function for streaming
        def generate():
            for chunk in audio_chunks:
                yield chunk

        # Set headers for streaming audio response
        headers = {
            'Content-Type': 'audio/wav',
            'X-Response-Text': response_text,
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Expose-Headers': 'X-Response-Text'
        }

        return Response(
            stream_with_context(generate()),
            mimetype='audio/wav',
            headers=headers
        )
    
    except Exception as e:
        logger.error(f"Error in voice response: {e}")
        response_text = "I'm sorry, I couldn't process your request." if 'response_text' not in locals() else locals()['response_text']
        return jsonify({
            'error': str(e),
            'response': response_text,
            'success': False
        }), 500

@app.route('/api/debug', methods=['GET', 'OPTIONS'])
def debug_info():
    """Debug endpoint to check API health"""
    if request.method == 'OPTIONS':
        return handle_options('')
        
    return jsonify({
        'status': 'running',
        'gemini_initialized': _model is not None,
        'tts_initialized': _pipeline is not None
    }) 