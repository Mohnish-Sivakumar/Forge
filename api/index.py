from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import google.generativeai as genai
import speech_recognition as sr
from kokoro import KPipeline
import numpy as np
import io
import logging
import soundfile as sf
import os
import traceback
import sys

app = Flask(__name__)
# Simplify CORS to ensure it works with Vercel
CORS(app, origins="*", supports_credentials=False)
logging.basicConfig(level=logging.DEBUG)

# Initialize services with API key
GEMINI_API_KEY = "AIzaSyDrxMRoQ-Knm7gM_6YNHAiPhXoC6HN09S4"
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    # Initialize the KPipeline safely
    try:
        pipeline = KPipeline(lang_code='a')  # Only supports basic initialization
        logging.info("Successfully initialized KPipeline")
    except Exception as e:
        logging.error(f"Error initializing KPipeline: {e}")
        pipeline = None
except Exception as e:
    logging.error(f"Error initializing Gemini: {e}")
    model = None

def process_text_chunk(text):
    try:
        if pipeline is None:
            logging.error("KPipeline not initialized")
            yield b''
            return
            
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
        logging.error(traceback.format_exc())
        yield b''

def generate_speech_chunks(text):
    chunks = [c.strip() + '.' for c in text.split('.') if c.strip()]
    for chunk in chunks:
        if chunk:
            for audio in process_text_chunk(chunk):
                if audio:
                    logging.debug("Yielding audio chunk")
                    yield audio

# Basic OPTIONS handler for all routes
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
    return "Welcome to the Voice Assistant API!"

# Simplified text response endpoint
@app.route('/api/text', methods=['POST', 'OPTIONS'])
def text_response():
    # Handle OPTIONS request
    if request.method == 'OPTIONS':
        return options_handler('')
        
    try:
        # Log the request for debugging
        logging.info(f"Received text request: {request.method} {request.path}")
        logging.info(f"Request headers: {dict(request.headers)}")
        
        # Check if Gemini model is initialized
        if model is None:
            logging.error("Gemini model not initialized")
            return jsonify({'error': 'Service temporarily unavailable'}), 503
            
        # Handle different request formats
        try:
            if request.is_json:
                data = request.json
            elif request.form:
                data = request.form.to_dict()
            elif request.data:
                import json
                data = json.loads(request.data)
            else:
                data = {}
        except Exception as e:
            logging.error(f"Failed to parse request data: {e}")
            data = {}
        
        user_input = data.get('text', '')
        logging.info(f"User input: {user_input}")
        
        if not user_input:
            return jsonify({'error': 'No input text provided'}), 400
            
        prompt = f"""
        Respond to: {user_input}
        Important: Provide your response as a continuous paragraph without line breaks or bullet points.
        Keep punctuation minimal, using mostly commas and periods. Your response must be concise and strictly limited to a maximum of 30 words. Remember you're an 
        interviewer. Ask the questions, and provide feedback after hearing the response from the user.
        Understand the context of the interview, and then ask a single question each time. After you hear the user's response, provide feedback on their response. Don't ask follow-up questions but tell them what specifically in their response was good and bad, why it was bad, and what could have been improved, and then move on to the next question.
        """
        
        logging.info("Generating response with Gemini")
        response_text = model.generate_content(prompt).text
        response_text = ' '.join(response_text.split())
        
        logging.info(f"Generated response: {response_text}")
        
        # Create a simple JSON response with CORS headers
        response = jsonify({'response': response_text})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    
    except Exception as e:
        logging.error(f"Error in text response: {e}")
        logging.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# Simplified voice endpoint
@app.route('/api/voice', methods=['POST', 'OPTIONS'])
def voice_assistant():
    # Handle OPTIONS request
    if request.method == 'OPTIONS':
        return options_handler('')
        
    try:
        # Log the request for debugging
        logging.info(f"Received voice request: {request.method} {request.path}")
        logging.info(f"Request headers: {dict(request.headers)}")
        
        # Check if Gemini model and pipeline are initialized
        if model is None:
            logging.error("Gemini model not initialized")
            return jsonify({'error': 'Service temporarily unavailable'}), 503
            
        if pipeline is None:
            logging.error("Speech pipeline not initialized")
            return jsonify({'error': 'Speech service temporarily unavailable'}), 503
        
        # Handle different request formats
        try:
            if request.is_json:
                data = request.json
            elif request.form:
                data = request.form.to_dict()
            elif request.data:
                import json
                data = json.loads(request.data)
            else:
                data = {}
        except Exception as e:
            logging.error(f"Failed to parse request data: {e}")
            data = {}
        
        user_input = data.get('text', '')
        logging.info(f"User input: {user_input}")
        
        if not user_input:
            return jsonify({'error': 'No input text provided'}), 400
            
        prompt = f"""
        Respond to: {user_input}
        Important: Provide your response as a continuous paragraph without line breaks or bullet points.
        Keep punctuation minimal, using mostly commas and periods. Your response must be concise and strictly limited to a maximum of 30 words. Remember you're an 
        interviewer. Ask the questions, and provide feedback after hearing the response from the user.
        Understand the context of the interview, and then ask a single question each time. After you hear the user's response, provide feedback on their response. Don't ask follow-up questions but tell them what specifically in their response was good and bad, why it was bad, and what could have been improved, and then move on to the next question.
        """
        
        logging.info("Generating response with Gemini")
        response_text = model.generate_content(prompt).text
        response_text = ' '.join(response_text.split())
        
        logging.info(f"Generated response: {response_text}")

        # Set simplified headers
        headers = {
            'Content-Type': 'audio/wav',
            'X-Response-Text': response_text,
            'Access-Control-Allow-Origin': '*'
        }

        logging.info("Generating speech")
        return Response(
            stream_with_context(generate_speech_chunks(response_text)),
            mimetype='audio/wav',
            headers=headers
        )

    except Exception as e:
        logging.error(f"Error: {e}")
        logging.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# Add a new debug route to help troubleshoot
@app.route('/api/debug', methods=['GET'])
def debug_info():
    info = {
        'gemini_initialized': model is not None,
        'pipeline_initialized': pipeline is not None,
        'environment': dict(os.environ),
        'python_version': '.'.join(map(str, [sys.version_info.major, sys.version_info.minor, sys.version_info.micro])) if 'sys' in globals() else "unknown"
    }
    return jsonify(info) 