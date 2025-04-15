from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import google.generativeai as genai
import logging
import json
import traceback
import os
import io
from kokoro import KPipeline
import soundfile as sf

# Initialize Flask app with simple CORS
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.DEBUG)

# Initialize Gemini AI
GEMINI_API_KEY = "AIzaSyDrxMRoQ-Knm7gM_6YNHAiPhXoC6HN09S4"
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    logging.info("Gemini AI initialized successfully")
except Exception as e:
    logging.error(f"Error initializing Gemini: {e}")
    model = None

# Initialize Kokoro TTS - do this lazily to avoid cold start issues
pipeline = None

def get_tts_pipeline():
    global pipeline
    if pipeline is None:
        try:
            logging.info("Initializing Kokoro TTS pipeline")
            pipeline = KPipeline(lang_code='a')  # Basic initialization
            logging.info("Kokoro TTS pipeline initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing Kokoro TTS: {e}")
            logging.error(traceback.format_exc())
            return None
    return pipeline

def process_text_chunk(text):
    """Process a chunk of text and convert to audio using Kokoro TTS"""
    try:
        tts_pipeline = get_tts_pipeline()
        if tts_pipeline is None:
            logging.error("TTS pipeline not available")
            yield b''
            return
            
        generator = tts_pipeline(text, voice='af_heart')
        for _, _, audio in generator:
            buffer = io.BytesIO()
            sf.write(buffer, audio, 24000, format='WAV')
            buffer.seek(0)
            audio_data = buffer.read()
            logging.debug(f"Generated audio chunk: {len(audio_data)} bytes")
            yield audio_data
    except Exception as e:
        logging.error(f"Error processing TTS chunk: {e}")
        logging.error(traceback.format_exc())
        yield b''

def generate_speech_chunks(text):
    """Split text into chunks and generate audio for each chunk"""
    # Split text into manageable chunks (by sentences)
    chunks = [c.strip() + '.' for c in text.split('.') if c.strip()]
    
    # If no chunks were created, use the whole text
    if not chunks:
        chunks = [text]
    
    logging.info(f"Processing {len(chunks)} text chunks for TTS")
    
    for i, chunk in enumerate(chunks):
        if chunk:
            logging.info(f"Processing chunk {i+1}/{len(chunks)}: {chunk[:30]}...")
            for audio in process_text_chunk(chunk):
                if audio:
                    yield audio

# Basic OPTIONS handler for CORS preflight requests
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    response.headers.add('Access-Control-Max-Age', '3600')
    return response

@app.route('/')
def home():
    return "Welcome to the Interview AI API! Server is running."

@app.route('/api/text', methods=['POST', 'OPTIONS'])
def text_response():
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        return options_handler('')
        
    try:
        # Log the request
        logging.info(f"Received text request: {request.method} {request.path}")
        
        # Check if Gemini model is initialized
        if model is None:
            logging.error("Gemini model not initialized")
            return jsonify({'error': 'AI service unavailable'}), 503
            
        # Parse request data
        try:
            if request.is_json:
                data = request.json
            elif request.form:
                data = request.form.to_dict()
            elif request.data:
                data = json.loads(request.data)
            else:
                data = {}
        except Exception as e:
            logging.error(f"Failed to parse request data: {e}")
            data = {}
        
        # Get user input
        user_input = data.get('text', '')
        logging.info(f"User input: {user_input}")
        
        if not user_input:
            return jsonify({'error': 'No input text provided'}), 400
            
        # Generate response with Gemini AI
        prompt = f"""
        Respond to: {user_input}
        Important: Provide your response as a continuous paragraph without line breaks or bullet points.
        Keep punctuation minimal, using mostly commas and periods. Your response must be concise and strictly limited to a maximum of 30 words. Remember you're an 
        interviewer. Ask the questions, and provide feedback after hearing the response from the user.
        Understand the context of the interview, and then ask a single question each time. After you hear the user's response, provide feedback on their response. Don't ask follow-up questions but tell them what specifically in their response was good and bad, why it was bad, and what could have been improved, and then move on to the next question.
        """
        
        response_text = model.generate_content(prompt).text
        response_text = ' '.join(response_text.split())
        
        logging.info(f"Generated response: {response_text}")
        
        # Return JSON response
        response = jsonify({'response': response_text})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    
    except Exception as e:
        logging.error(f"Error in text response: {e}")
        logging.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice', methods=['POST', 'OPTIONS'])
def voice_response():
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        return options_handler('')
        
    try:
        # Log the request
        logging.info(f"Received voice request: {request.method} {request.path}")
        
        # Check if Gemini model is initialized
        if model is None:
            logging.error("Gemini model not initialized")
            return jsonify({'error': 'AI service unavailable'}), 503
        
        # Parse request data
        try:
            if request.is_json:
                data = request.json
            elif request.form:
                data = request.form.to_dict()
            elif request.data:
                data = json.loads(request.data)
            else:
                data = {}
        except Exception as e:
            logging.error(f"Failed to parse request data: {e}")
            data = {}
        
        # Get user input
        user_input = data.get('text', '')
        logging.info(f"User input: {user_input}")
        
        if not user_input:
            return jsonify({'error': 'No input text provided'}), 400
        
        # Generate response with Gemini AI
        prompt = f"""
        Respond to: {user_input}
        Important: Provide your response as a continuous paragraph without line breaks or bullet points.
        Keep punctuation minimal, using mostly commas and periods. Your response must be concise and strictly limited to a maximum of 30 words. Remember you're an 
        interviewer. Ask the questions, and provide feedback after hearing the response from the user.
        Understand the context of the interview, and then ask a single question each time. After you hear the user's response, provide feedback on their response. Don't ask follow-up questions but tell them what specifically in their response was good and bad, why it was bad, and what could have been improved, and then move on to the next question.
        """
        
        response_text = model.generate_content(prompt).text
        response_text = ' '.join(response_text.split())
        
        logging.info(f"Generated response: {response_text}")

        # Initialize TTS pipeline if needed
        tts_pipeline = get_tts_pipeline()
        if tts_pipeline is None:
            logging.error("TTS pipeline not available, falling back to text-only response")
            return jsonify({
                'response': response_text,
                'error': 'TTS not available',
                'success': False
            })

        # Set headers for streaming audio response
        headers = {
            'Content-Type': 'audio/wav',
            'X-Response-Text': response_text,
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Expose-Headers': 'X-Response-Text'
        }

        logging.info("Starting TTS audio generation and streaming")
        return Response(
            stream_with_context(generate_speech_chunks(response_text)),
            mimetype='audio/wav',
            headers=headers
        )
    
    except Exception as e:
        logging.error(f"Error in voice response: {e}")
        logging.error(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'response': None,
            'success': False
        }), 500

@app.route('/api/debug', methods=['GET'])
def debug_info():
    """Debug endpoint to check API health and configuration"""
    tts_status = "not_initialized"
    if pipeline is not None:
        tts_status = "initialized"
        
    info = {
        'status': 'running',
        'gemini_initialized': model is not None,
        'tts_status': tts_status,
        'environment': {k: v for k, v in dict(os.environ).items() 
                        if not k.startswith('AWS_') and not k.startswith('VERCEL_')},
        'python_version': os.environ.get('PYTHONVERSION', 'unknown')
    }
    return jsonify(info) 