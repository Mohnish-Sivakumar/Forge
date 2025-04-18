from flask import Flask, request, jsonify, Response, send_from_directory, stream_with_context
from flask_cors import CORS
import google.generativeai as genai
import kokoro
import logging
import os
import io
import json
import base64
import numpy as np
import struct

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

# Initialize Kokoro TTS pipeline
pipeline = kokoro.KPipeline(lang_code='a')  # American English

# Configure available voices - Using actual Kokoro voice IDs
AVAILABLE_VOICES = {
    'default': 'af_heart',             # Default English voice
    'female1': 'af_sarah',             # Female voice 1
    'female2': 'af_nicole',            # Female emotional voice
    'male1': 'am_michael',             # Male narrative voice 
    'male2': 'am_adam',                # Male conversational voice
    'british': 'bf_isabella',          # British English voice
    'australian': 'bf_emma',           # Australian English voice
}

def text_to_speech(text, voice='default'):
    """Convert text to speech using Kokoro"""
    app.logger.info(f"Generating voice for text using voice: {voice}")
    
    # Select voice from available options
    voice_id = AVAILABLE_VOICES.get(voice, AVAILABLE_VOICES['default'])
    app.logger.info(f"Selected Kokoro voice ID: {voice_id}")
    
    try:
        # Process text to clean it for better speech generation
        processed_text = text.replace('\n', ' ').strip()
        
        # Generate audio chunks
        audio_chunks = []
        
        # Log parameters for debugging
        app.logger.info(f"Calling Kokoro pipeline with text length: {len(processed_text)}")
        app.logger.info(f"Text preview: {processed_text[:50]}...")
        
        # Use a try/except specifically for the pipeline call
        try:
            generator = pipeline(processed_text, voice=voice_id, split_pattern=None)
            
            for i, (gs, ps, audio_data) in enumerate(generator):
                app.logger.info(f"Processing chunk {i+1}: graphemes={len(gs)}, phonemes={len(ps)}")
                
                if audio_data is not None:
                    # Convert PyTorch tensor to numpy array if needed
                    if hasattr(audio_data, 'detach') and callable(audio_data.detach):
                        # This is a PyTorch tensor
                        try:
                            audio_data = audio_data.detach().cpu().numpy()
                            app.logger.info(f"Converted PyTorch tensor to numpy array, shape: {audio_data.shape}")
                        except Exception as e:
                            app.logger.error(f"Error converting PyTorch tensor to numpy: {e}")
                            continue
                    
                    # Ensure audio_data is a numpy array or bytes
                    if not hasattr(audio_data, 'tobytes') and not isinstance(audio_data, bytes):
                        app.logger.warning(f"Unexpected audio data type: {type(audio_data)}")
                        try:
                            # Try to convert to bytes
                            audio_data = bytes(audio_data)
                            app.logger.info(f"Converted {type(audio_data)} to bytes, size: {len(audio_data)}")
                        except Exception as e:
                            app.logger.error(f"Error converting audio data to bytes: {e}")
                            continue
                    
                    audio_chunks.append(audio_data)
                    app.logger.info(f"Added audio chunk {i+1}, total chunks: {len(audio_chunks)}")
                else:
                    app.logger.warning(f"Received None audio data for chunk {i+1}")
        except Exception as pipeline_error:
            app.logger.error(f"Error in Kokoro pipeline: {pipeline_error}")
            app.logger.error(f"Text that caused the error: '{processed_text}'")
            app.logger.error(f"Voice ID that caused the error: '{voice_id}'")
            raise
        
        app.logger.info(f"Generated {len(audio_chunks)} audio chunks")
        return audio_chunks
    except Exception as e:
        app.logger.error(f"Error generating speech: {e}")
        # Check if it's a 404 error for the voice file
        if "404 Client Error" in str(e) and "voices/" in str(e):
            app.logger.warning(f"Voice file not found: {voice_id}. This is normal if you haven't downloaded the voice files.")
        return []

def create_wav_header(data_size, sample_rate=22050, channels=1, bits_per_sample=16):
    """Create a proper WAV file header"""
    # Calculate sizes
    bytes_per_sample = bits_per_sample // 8
    block_align = channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    
    # RIFF chunk descriptor
    header = bytearray()
    header.extend(b'RIFF')
    header.extend((36 + data_size).to_bytes(4, byteorder='little'))  # File size - 8 bytes
    header.extend(b'WAVE')
    
    # 'fmt ' sub-chunk
    header.extend(b'fmt ')
    header.extend((16).to_bytes(4, byteorder='little'))  # Subchunk1Size (16 for PCM)
    header.extend((1).to_bytes(2, byteorder='little'))   # AudioFormat (1 for PCM)
    header.extend(channels.to_bytes(2, byteorder='little'))  # NumChannels
    header.extend(sample_rate.to_bytes(4, byteorder='little'))  # SampleRate
    header.extend(byte_rate.to_bytes(4, byteorder='little'))  # ByteRate
    header.extend(block_align.to_bytes(2, byteorder='little'))  # BlockAlign
    header.extend(bits_per_sample.to_bytes(2, byteorder='little'))  # BitsPerSample
    
    # 'data' sub-chunk
    header.extend(b'data')
    header.extend(data_size.to_bytes(4, byteorder='little'))
    
    return bytes(header)

def prepare_audio_chunks(audio_chunks):
    """Prepare audio chunks for streaming or encoding as base64"""
    # Initialize bytearrays for headers and data
    processed_chunks = []
    sample_rate = 22050  # Kokoro's default sample rate
    
    try:
        # First pass to calculate total size and convert all chunks to bytes
        total_data_size = 0
        chunk_bytes_list = []
        
        for chunk in audio_chunks:
            # Convert numpy arrays to int16 bytes
            if hasattr(chunk, 'tobytes'):
                # Normalize numpy array if needed
                max_val = np.max(np.abs(chunk))
                if max_val > 1.0 and max_val <= 32767:
                    # Already in int16 range
                    chunk_bytes = chunk.astype(np.int16).tobytes()
                elif max_val > 0:
                    # Float array in range [-1, 1], convert to int16
                    chunk_bytes = (chunk * 32767).astype(np.int16).tobytes()
                else:
                    # Empty or zero array
                    chunk_bytes = np.zeros(1, dtype=np.int16).tobytes()
            elif isinstance(chunk, bytes):
                chunk_bytes = chunk
            else:
                # Skip chunks we can't process
                app.logger.warning(f"Skipping chunk of unsupported type: {type(chunk)}")
                continue
                
            chunk_bytes_list.append(chunk_bytes)
            total_data_size += len(chunk_bytes)
        
        # If we're combining all chunks (for base64 encoding)
        if total_data_size > 0:
            # Create WAV header for the combined data
            wav_header = create_wav_header(total_data_size, sample_rate=sample_rate)
            
            # Append header to the first chunk
            if chunk_bytes_list:
                processed_chunks.append(wav_header)
                processed_chunks.extend(chunk_bytes_list)
        
        return processed_chunks
    except Exception as e:
        app.logger.error(f"Error preparing audio chunks: {e}")
        return []

def chunk_text(text, max_length=300):
    """Split text into smaller chunks, trying to break at sentence boundaries."""
    # If text is already small enough, return it as is
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    # Common sentence ending punctuation
    sentence_enders = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
    
    while len(text) > max_length:
        # Find the last sentence boundary within max_length
        chunk_end = max_length
        found_boundary = False
        
        # Try to find a natural break point
        for ender in sentence_enders:
            last_index = text[:max_length].rfind(ender)
            if last_index > 0:
                # Include the punctuation mark
                chunk_end = last_index + len(ender)
                found_boundary = True
                break
        
        # If no sentence boundary found, try to break at a comma
        if not found_boundary:
            last_comma = text[:max_length].rfind(', ')
            if last_comma > 0:
                chunk_end = last_comma + 2  # Include the comma and space
            else:
                # If no comma, try to break at a space
                last_space = text[:max_length].rfind(' ')
                if last_space > max_length // 2:  # Only break at space if it's not too early
                    chunk_end = last_space + 1
        
        # Extract the chunk and add to result
        chunk = text[:chunk_end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move to the rest of the text
        text = text[chunk_end:].strip()
    
    # Add the remaining text as the last chunk
    if text:
        chunks.append(text)
    
    app.logger.info(f"Split text into {len(chunks)} chunks")
    return chunks

# Health check endpoint
@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({"status": "healthy"})

# Simple test endpoint that always works
@app.route('/api/test', methods=['GET', 'POST', 'OPTIONS'])
def test_endpoint():
    """Simple test endpoint that always returns success"""
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    app.logger.debug("Test endpoint called with method: %s", request.method)
    app.logger.debug("Headers: %s", request.headers)
    
    # Return different responses based on method
    if request.method == 'GET':
        return jsonify({
            "status": "success", 
            "message": "API is working correctly", 
            "method": "GET"
        })
    
    elif request.method == 'POST':
        try:
            # Try to parse JSON if present
            if request.is_json:
                data = request.get_json()
                app.logger.debug("Received data: %s", data)
                return jsonify({
                    "status": "success",
                    "message": "Test endpoint received POST data successfully",
                    "method": "POST",
                    "received_data": data
                })
            else:
                return jsonify({
                    "status": "success",
                    "message": "Test endpoint received POST request without JSON data",
                    "method": "POST"
                })
        except Exception as e:
            app.logger.error("Error in test endpoint: %s", str(e))
            return jsonify({"status": "error", "message": str(e)}), 500

# Debug endpoint to verify API is working
@app.route('/api/debug', methods=['GET', 'OPTIONS'])
def debug():
    """Simple debug endpoint that always returns a successful response"""
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    # Log request details to help with debugging
    app.logger.info(f"Debug request received from: {request.headers.get('Origin', 'unknown')}")
    
    # Return a simple JSON response
    return jsonify({
        "status": "success",
        "message": "API debug endpoint is working",
        "endpoints": ["/api/text", "/api/voice", "/api/login"]
    })

# API and frontend routes
@app.route('/')
def home():
    if SERVE_STATIC:
        app.logger.info("Serving static files from: %s", app.static_folder)
        return send_from_directory(app.static_folder, 'index.html')
    return jsonify({"message": "API is running"})

# Serve static files for frontend routes
@app.route('/<path:path>')
def serve_static(path):
    if SERVE_STATIC:
        if path.startswith('api/'):
            # Don't try to serve API calls as static files
            return jsonify({"error": "Not found"}), 404
            
        # Check specifically for CSS/JS/media files
        if path.endswith(('.js', '.css', '.png', '.jpg', '.svg', '.ico', '.json')):
            app.logger.info(f"Serving static file: {path}")
            if os.path.exists(os.path.join(app.static_folder, path)):
                return send_from_directory(app.static_folder, path)
        
        # For React routing - serve index.html for any path not found
        app.logger.info(f"Serving index.html for path: {path}")
        return send_from_directory(app.static_folder, 'index.html')
        
    return jsonify({"error": "Not found"}), 404

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

# Voice API endpoint with Kokoro
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
        
        # Check if the response is too long and should be chunked
        text_chunks = chunk_text(response_text)
        all_audio_chunks = []
        
        # Process each text chunk separately
        for chunk_idx, text_chunk in enumerate(text_chunks):
            app.logger.info(f"Processing chunk {chunk_idx+1}/{len(text_chunks)}, length: {len(text_chunk)}")
            
            # Get audio chunks for this text chunk
            chunk_audio = text_to_speech(text_chunk, voice=voice_option)
            if chunk_audio:
                all_audio_chunks.extend(chunk_audio)
        
        if not all_audio_chunks:
            logging.warning("No audio chunks generated, returning text-only response")
            return jsonify({
                "status": "partial_success", 
                "message": "Text generated successfully, but audio generation failed. This is expected if you haven't downloaded voice files.",
                "response": response_text,
                "fallback": True
            })
            
        # Prepare the audio chunks
        processed_chunks = prepare_audio_chunks(all_audio_chunks)
        
        if not processed_chunks:
            logging.warning("Failed to process audio chunks, returning text-only response")
            return jsonify({
                "status": "partial_success", 
                "message": "Text generated successfully, but audio processing failed.",
                "response": response_text,
                "fallback": True
            })
        
        # When explicitly requesting JSON or we're running on Render
        # return base64 encoded audio in JSON format which works better with certain platforms
        if format_preference == 'json' or os.environ.get('RENDER', '').lower() == 'true':
            try:
                # Combine all chunks into a single byte array
                combined_audio = b''.join(processed_chunks)
                
                # Check audio size and log warning if it's very large
                audio_size_kb = len(combined_audio) / 1024
                app.logger.info(f"Generated audio size: {audio_size_kb:.2f} KB")
                
                if audio_size_kb > 500:  # More than 500KB may cause issues
                    app.logger.warning(f"Audio size is large ({audio_size_kb:.2f} KB), which may cause playback issues")
                
                audio_base64 = base64.b64encode(combined_audio).decode('utf-8')
                
                # Return JSON response with base64 encoded audio
                return jsonify({
                    "status": "success",
                    "response": response_text,
                    "audio": audio_base64,
                    "format": "base64"
                })
            except Exception as audio_error:
                logging.error(f"Error processing audio for JSON response: {audio_error}")
                return jsonify({
                    "status": "partial_success",
                    "message": f"Audio processing error: {str(audio_error)}",
                    "response": response_text,
                    "fallback": True
                })
        
        # Otherwise, stream the audio response (default for local development)
        def generate_audio():
            # Yield each chunk as bytes
            for chunk in processed_chunks:
                if isinstance(chunk, bytes):
                    yield chunk
                else:
                    # Fallback in case something went wrong with processing
                    app.logger.warning(f"Non-bytes chunk found during streaming: {type(chunk)}")
                    try:
                        yield bytes(chunk)
                    except Exception as e:
                        app.logger.error(f"Error converting chunk to bytes: {e}")
        
        # Set headers with the text response for display
        headers = {
            'Content-Type': 'audio/wav',
            'X-Response-Text': response_text,
            'Access-Control-Expose-Headers': 'X-Response-Text'
        }

        return Response(
            stream_with_context(generate_audio()),
            mimetype='audio/wav',
            headers=headers
        )

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
    
    response = jsonify({})
    response.headers.add("Access-Control-Allow-Origin", origin)
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    response.headers.add("Access-Control-Expose-Headers", "X-Response-Text")
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port) 