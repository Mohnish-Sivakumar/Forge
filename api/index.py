import json
import os
import sys
import base64
from http.server import BaseHTTPRequestHandler
import logging
import google.generativeai as genai
import io
import traceback
import time
import requests
import numpy as np  # Add numpy import for audio processing
import struct  # For creating WAV file header
import re  # For splitting text into chunks
import urllib.parse
from urllib.request import urlopen, Request
import http.client

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('app')

# Global flags for memory optimization
LOW_MEMORY_MODE = os.environ.get('LOW_MEMORY_MODE', 'true').lower() == 'true'
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# Optional imports - only load when needed
google_ai = None
kokoro = None
torch = None
numpy = None

def load_gemini():
    global google_ai
    if google_ai is None:
        try:
            import google.generativeai as genai
            google_ai = genai
            google_ai.configure(api_key=GEMINI_API_KEY)
            logger.info("Google Generative AI loaded successfully")
            return True
        except ImportError:
            logger.error("Failed to import Google Generative AI")
            return False
    return True

def load_tts_dependencies():
    global kokoro, torch, numpy
    if kokoro is None or torch is None or numpy is None:
        try:
            # Only import if needed
            import kokoro as k
            import torch as t
            import numpy as np
            kokoro = k
            torch = t
            numpy = np
            logger.info("TTS dependencies loaded successfully")
            return True
        except ImportError as e:
            logger.error(f"Failed to import TTS dependencies: {e}")
            return False
    return True

def download_voice_file(voice_id):
    """Downloads a voice file from HuggingFace if it doesn't exist locally"""
    if LOW_MEMORY_MODE:
        logger.info("Skipping voice file download in low memory mode")
        return False
        
    # Only try to download if we have the required libraries
    if not load_tts_dependencies():
        return False
        
    try:
        voices_dir = os.path.join(os.path.dirname(__file__), 'voice_files')
        os.makedirs(voices_dir, exist_ok=True)
        
        voice_path = os.path.join(voices_dir, f"{voice_id}.pt")
        
        # Return early if file exists
        if os.path.exists(voice_path) and os.path.getsize(voice_path) > 0:
            logger.info(f"Voice file {voice_id}.pt already exists")
            return True
            
        # Download from HuggingFace
        logger.info(f"Downloading voice file {voice_id}.pt from HuggingFace")
        
        return kokoro.synthesizer.download_speaker_file(voice_id, voices_dir)
    except Exception as e:
        logger.error(f"Error downloading voice file: {e}")
        return False

def get_voice_file(voice_id):
    """Returns path to voice file, downloads if needed"""
    if LOW_MEMORY_MODE:
        logger.info("Skipping voice file in low memory mode")
        return None
        
    try:
        voices_dir = os.path.join(os.path.dirname(__file__), 'voice_files')
        os.makedirs(voices_dir, exist_ok=True)
        
        voice_path = os.path.join(voices_dir, f"{voice_id}.pt")
        
        # If file doesn't exist, try to download it
        if not os.path.exists(voice_path) or os.path.getsize(voice_path) == 0:
            success = download_voice_file(voice_id)
            if not success:
                logger.warning(f"Couldn't get voice file for {voice_id}")
                return None
                
        return voice_path
    except Exception as e:
        logger.error(f"Error getting voice file: {e}")
        return None

def list_available_voices():
    """Lists available voice files"""
    try:
        if LOW_MEMORY_MODE:
            # Return predefined list in low memory mode
            return ["default", "female1", "female2", "male1", "male2", "british", "australian"]
            
        voices_dir = os.path.join(os.path.dirname(__file__), 'voice_files')
        if os.path.exists(voices_dir):
            voices = [f.split('.')[0] for f in os.listdir(voices_dir) if f.endswith('.pt')]
            return voices if voices else ["default"]
        return ["default"]
    except Exception as e:
        logger.error(f"Error listing voices: {e}")
        return ["default"]

def text_to_speech(text, voice_option='default'):
    """Convert text to speech using Kokoro TTS or fallback"""
    if not text:
        logger.warning("Empty text provided to TTS")
        return None, None
        
    # Use simpler response in low memory mode
    if LOW_MEMORY_MODE:
        logger.info("Using text-only mode due to memory constraints")
        return None, {"message": "Voice generation is disabled in low-memory mode"}
        
    # Only try TTS if we have the required libraries
    if not load_tts_dependencies():
        logger.warning("TTS dependencies not available")
        return None, {"error": "TTS dependencies not available"}
    
    try:
        # Map voice option to Kokoro voice ID
        voice_mapping = {
            'default': 'af_heart',       # Default female voice
            'female1': 'af_grace',       # Alternative female voice
            'female2': 'af_heart',       # Emotional female voice
            'male1': 'am_michael',       # Narrative male voice
            'male2': 'am_adam',          # Conversational male voice
            'british': 'br_daniel',      # British male voice
            'australian': 'au_charlotte' # Australian female voice
        }
        
        voice_id = voice_mapping.get(voice_option, 'af_heart')
        logger.info(f"Selected Kokoro voice ID: {voice_id}")
        
        # Get the voice file
        voice_file = get_voice_file(voice_id)
        if not voice_file:
            logger.warning(f"Voice file not available for {voice_id}")
            return None, {"error": f"Voice {voice_option} not available"}
            
        # Split long text into chunks if needed
        chunks = []
        if len(text) > 300:
            # Simple chunking by sentences
            sentences = text.replace('. ', '.|').replace('! ', '!|').replace('? ', '?|').split('|')
            chunk = ""
            for sentence in sentences:
                if len(chunk) + len(sentence) < 300:
                    chunk += sentence + " "
                else:
                    if chunk:
                        chunks.append(chunk.strip())
                    chunk = sentence + " "
            if chunk:
                chunks.append(chunk.strip())
        else:
            chunks = [text]
            
        logger.info(f"Processing {len(chunks)} chunk(s)")
        
        all_audio = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}: graphemes={len(chunk)}, phonemes={len(chunk)}")
            
            # Generate audio using Kokoro
            pipeline = kokoro.synthesizer.Synthesizer(voice_file)
            audio_tensor = pipeline.synthesize(chunk)
            
            # Convert to numpy array and then to list
            audio_array = audio_tensor.detach().cpu().numpy()
            logger.info(f"Converted PyTorch tensor to numpy array, shape: {audio_array.shape}")
            
            all_audio.append(audio_array)
            
        # Combine audio chunks if needed
        if len(all_audio) > 1:
            combined_audio = numpy.concatenate(all_audio)
        else:
            combined_audio = all_audio[0]
            
        # Create WAV file
        wav_data = create_wav_file(combined_audio, 22050)
        
        # Encode to base64
        encoded_audio = base64.b64encode(wav_data).decode('utf-8')
        
        return encoded_audio, None
        
    except Exception as e:
        logger.error(f"Error in text-to-speech: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None, {"error": str(e)}

def create_wav_file(audio_array, sample_rate):
    """Creates a WAV file from audio data"""
    try:
        import io
        import wave
        import struct
        
        # Create WAV file in memory
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Convert float32 to int16
            audio_array = (audio_array * 32767).astype(numpy.int16)
            
            # Write audio data
            for sample in audio_array:
                wav_file.writeframes(struct.pack('<h', sample))
                
        # Get the WAV data
        buffer.seek(0)
        wav_data = buffer.read()
        
        return wav_data
        
    except Exception as e:
        logger.error(f"Error creating WAV file: {e}")
        return None

class handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Request-With')
        self.send_header('Access-Control-Expose-Headers', 'X-Response-Text')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        
    def do_GET(self):
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            
            # Handle different endpoints
            if parsed_path.path == '/api/debug':
                try:
                    # Debug endpoint to check status
                    response_data = {
                        'status': 'ok',
                        'endpoints': ['/api/text', '/api/voice', '/api/login'],
                        'low_memory_mode': LOW_MEMORY_MODE,
                        'available_voices': list_available_voices(),
                        'gemini_api_configured': bool(GEMINI_API_KEY),
                    }
                    
                    # Check if TTS is available
                    if not LOW_MEMORY_MODE:
                        tts_available = load_tts_dependencies()
                        response_data['tts_available'] = tts_available
                        
                    self.send_response(200)
                    self._set_cors_headers()
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode())
                    return
                    
                except Exception as e:
                    logger.error(f"Error in debug endpoint: {e}")
                    self.send_response(500)
                    self._set_cors_headers()
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': str(e)}).encode())
                    return
                    
            elif parsed_path.path == '/api/text' or parsed_path.path == '/api/voice':
                # Simple GET response for these endpoints
                response_data = {
                    'message': 'Please use POST method for this endpoint',
                    'endpoint': parsed_path.path,
                    'documentation': 'Send a POST request with JSON body containing "text" field'
                }
                self.send_response(200)
                self._set_cors_headers()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode())
                return
                
            # Default handling for unknown endpoints
            self.send_response(404)
            self._set_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Endpoint not found'}).encode())
                
        except Exception as e:
            logger.error(f"Error handling GET request: {e}")
            self.send_response(500)
            self._set_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
            
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(post_data) if post_data else {}
            except json.JSONDecodeError:
                data = {}
                
            parsed_path = urllib.parse.urlparse(self.path)
            
            # Handle different endpoints
            if parsed_path.path == '/api/text':
                self._handle_text_request(data)
            elif parsed_path.path == '/api/voice':
                self._handle_voice_request(data, self.headers.get('Content-Type', ''))
            elif parsed_path.path == '/api/login':
                self._handle_login_request(data)
            else:
                self.send_response(404)
                self._set_cors_headers()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Endpoint not found'}).encode())
                
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
            self.send_response(500)
            self._set_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
            
    def _handle_text_request(self, post_data):
        try:
            text = post_data.get('text', '')
            if not text:
                self.send_response(400)
                self._set_cors_headers()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No text provided'}).encode())
                return
                
            # Load Gemini dependencies on demand
            if not load_gemini():
                generated_text = "I'm sorry, I can't process your request right now. The AI text generation service is unavailable."
            else:
                # Generate response using Google Generative AI
                model = google_ai.GenerativeModel('gemini-pro')
                result = model.generate_content(text)
                generated_text = result.text
                
            # Log the generated text
            logging.info(f"Generated text response: {generated_text[:100]}...")
            
            # Send response
            self.send_response(200)
            self._set_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.send_header('X-Response-Text', generated_text[:100] + '...')
            self.end_headers()
            
            response_data = {
                'response': generated_text,
                'status': 'success'
            }
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            logger.error(f"Error in text request: {e}")
            self.send_response(500)
            self._set_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
            
    def _handle_voice_request(self, post_data, content_type):
        try:
            text = post_data.get('text', '')
            if not text:
                self.send_response(400)
                self._set_cors_headers()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No text provided'}).encode())
                return
                
            voice = post_data.get('voice', 'default')
            
            # Generate text response if needed using Google Generative AI
            if post_data.get('generate_text', False):
                if not load_gemini():
                    generated_text = "I'm sorry, I can't process your request right now. The AI text generation service is unavailable."
                else:
                    model = google_ai.GenerativeModel('gemini-pro')
                    result = model.generate_content(text)
                    generated_text = result.text
            else:
                # Use the input text directly
                generated_text = text
                
            # Log the text to be spoken
            logging.info(f"Generated voice response: {generated_text}")
            
            # Convert text to speech
            audio_base64, error = text_to_speech(generated_text, voice)
            
            # If we have error but no audio, return error
            if error and not audio_base64:
                self.send_response(500 if 'error' in error else 200)
                self._set_cors_headers()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(error).encode())
                return
                
            # Prepare response headers
            self.send_response(200)
            self._set_cors_headers()
            
            # Prepare response based on requested format
            response_format = post_data.get('format', '').lower()
            
            # If we have audio data, return it
            if audio_base64:
                if response_format == 'json':
                    # Send JSON response with base64 audio
                    self.send_header('Content-type', 'application/json')
                    self.send_header('X-Response-Text', generated_text[:100] + '...')
                    self.end_headers()
                    
                    response_data = {
                        'audio': audio_base64,
                        'text': generated_text,
                        'status': 'success',
                        'compressed': False
                    }
                    self.wfile.write(json.dumps(response_data).encode())
                else:
                    # Send binary audio data
                    self.send_header('Content-type', 'audio/wav')
                    self.send_header('X-Response-Text', generated_text[:100] + '...')
                    self.end_headers()
                    
                    # Decode base64 to binary
                    audio_binary = base64.b64decode(audio_base64)
                    self.wfile.write(audio_binary)
            else:
                # Fallback to JSON response with text
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Response-Text', generated_text[:100] + '...')
                self.end_headers()
                
                response_data = {
                    'text': generated_text,
                    'status': 'success',
                    'message': 'Voice synthesis unavailable, text only response provided'
                }
                
                if error:
                    response_data.update(error)
                    
                self.wfile.write(json.dumps(response_data).encode())
                
        except Exception as e:
            logger.error(f"Error in voice request: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            self.send_response(500)
            self._set_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response_data = {
                'error': str(e),
                'text': post_data.get('text', ''),
                'status': 'error'
            }
            self.wfile.write(json.dumps(response_data).encode())
            
    def _handle_login_request(self, post_data):
        try:
            username = post_data.get('username', '')
            password = post_data.get('password', '')
            
            # Simple mock login - not for real authentication
            if username == 'test' and password == 'password':
                response_data = {
                    'status': 'success',
                    'message': 'Login successful',
                    'user': {
                        'id': '12345',
                        'username': username,
                        'role': 'tester'
                    }
                }
                self.send_response(200)
            else:
                response_data = {
                    'status': 'error',
                    'message': 'Invalid username or password'
                }
                self.send_response(401)
                
            self._set_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            logger.error(f"Error in login request: {e}")
            self.send_response(500)
            self._set_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

def test(event, context):
    """
    Handle requests for Vercel serverless functions.
    """
    # Path is in the format: /api/endpoint
    # Method is GET, POST, etc.
    path = event.get('path', '')
    method = event.get('method', '').upper()
    
    logger.info(f"Received {method} request for {path}")
    
    # Parse request body if present
    body = event.get('body', '')
    headers = event.get('headers', {})
    
    try:
        # Create HTTP request handler
        handler_instance = handler()
        handler_instance.path = path
        handler_instance.headers = headers
        
        # Handle OPTIONS request for CORS
        if method == 'OPTIONS':
            return generate_response(200, {'message': 'CORS preflight response'})
            
        # Handle GET request
        elif method == 'GET':
            parsed_path = urllib.parse.urlparse(path)
            
            # Debug endpoint
            if parsed_path.path == '/api/debug':
                response_data = {
                    'status': 'ok',
                    'endpoints': ['/api/text', '/api/voice', '/api/login'],
                    'low_memory_mode': LOW_MEMORY_MODE,
                    'available_voices': list_available_voices(),
                    'gemini_api_configured': bool(GEMINI_API_KEY),
                }
                
                # Check if TTS is available
                if not LOW_MEMORY_MODE:
                    tts_available = load_tts_dependencies()
                    response_data['tts_available'] = tts_available
                    
                return generate_response(200, response_data)
                
            # Simple GET response for API endpoints
            elif parsed_path.path == '/api/text' or parsed_path.path == '/api/voice':
                return generate_response(200, {
                    'message': 'Please use POST method for this endpoint',
                    'endpoint': parsed_path.path,
                    'documentation': 'Send a POST request with JSON body containing "text" field'
                })
                
            # Default response for unknown endpoints
            return generate_response(404, {'error': 'Endpoint not found'})
            
        # Handle POST request
        elif method == 'POST':
            if not body:
                return generate_response(400, {'error': 'No request body provided'})
                
            # Parse body if it's a string
            data = json.loads(body) if isinstance(body, str) else body
            
            parsed_path = urllib.parse.urlparse(path)
            content_type = headers.get('content-type', '')
            
            # Handle different endpoints
            if parsed_path.path == '/api/text':
                return handle_text_request(data)
            elif parsed_path.path == '/api/voice':
                return handle_voice_request(data, content_type)
            elif parsed_path.path == '/api/login':
                return handle_login_request(data)
            else:
                return generate_response(404, {'error': 'Endpoint not found'})
                
        # Handle unsupported methods
        else:
            return generate_response(405, {'error': 'Method not allowed'})
            
    except Exception as e:
        logger.error(f"Error handling request: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return generate_response(500, {'error': str(e)})

def generate_response(status_code, body):
    """
    Generate a response object for Vercel serverless functions.
    """
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Request-With',
        'Content-Type': 'application/json'
    }
    
    if isinstance(body, dict) or isinstance(body, list):
        body = json.dumps(body)
        
    return {
        'statusCode': status_code,
        'headers': headers,
        'body': body
    }

def handle_text_request(data):
    """Handle text request for serverless function"""
    text = data.get('text', '')
    if not text:
        return generate_response(400, {'error': 'No text provided'})
        
    # Load Gemini dependencies on demand
    if not load_gemini():
        generated_text = "I'm sorry, I can't process your request right now. The AI text generation service is unavailable."
    else:
        # Generate response using Google Generative AI
        model = google_ai.GenerativeModel('gemini-pro')
        result = model.generate_content(text)
        generated_text = result.text
        
    # Log the generated text
    logging.info(f"Generated text response: {generated_text[:100]}...")
    
    response_data = {
        'response': generated_text,
        'status': 'success'
    }
    
    return generate_response(200, response_data)

def handle_voice_request(data, content_type):
    """Handle voice request for serverless function"""
    text = data.get('text', '')
    if not text:
        return generate_response(400, {'error': 'No text provided'})
        
    voice = data.get('voice', 'default')
    
    # Generate text response if needed using Google Generative AI
    if data.get('generate_text', False):
        if not load_gemini():
            generated_text = "I'm sorry, I can't process your request right now. The AI text generation service is unavailable."
        else:
            model = google_ai.GenerativeModel('gemini-pro')
            result = model.generate_content(text)
            generated_text = result.text
    else:
        # Use the input text directly
        generated_text = text
        
    # Log the text to be spoken
    logging.info(f"Generated voice response: {generated_text}")
    
    # Convert text to speech
    audio_base64, error = text_to_speech(generated_text, voice)
    
    # If we have error but no audio, return error
    if error and not audio_base64:
        status_code = 500 if 'error' in error else 200
        return generate_response(status_code, error)
        
    # Prepare response based on requested format
    response_format = data.get('format', '').lower()
    
    # If we have audio data, return it
    if audio_base64:
        if response_format == 'json' or not audio_base64:
            # Send JSON response with base64 audio
            response_data = {
                'audio': audio_base64,
                'text': generated_text,
                'status': 'success',
                'compressed': False
            }
            return generate_response(200, response_data)
        else:
            # For binary responses, we'd need special handling in Vercel
            # For now, always return JSON for serverless
            response_data = {
                'audio': audio_base64,
                'text': generated_text,
                'status': 'success',
                'compressed': False
            }
            return generate_response(200, response_data)
    else:
        # Fallback to JSON response with text
        response_data = {
            'text': generated_text,
            'status': 'success',
            'message': 'Voice synthesis unavailable, text only response provided'
        }
        
        if error:
            response_data.update(error)
            
        return generate_response(200, response_data)

def handle_login_request(data):
    """Handle login request for serverless function"""
    username = data.get('username', '')
    password = data.get('password', '')
    
    # Simple mock login - not for real authentication
    if username == 'test' and password == 'password':
        response_data = {
            'status': 'success',
            'message': 'Login successful',
            'user': {
                'id': '12345',
                'username': username,
                'role': 'tester'
            }
        }
        status_code = 200
    else:
        response_data = {
            'status': 'error',
            'message': 'Invalid username or password'
        }
        status_code = 401
        
    return generate_response(status_code, response_data) 