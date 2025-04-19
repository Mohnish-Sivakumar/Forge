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

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('app')

# Configure the generative AI model with the API key
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    logger.error("GOOGLE_API_KEY not found in environment variables")
    api_key = "your-api-key-here"  # Fallback for testing, replace with your key

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

# Create directory for voice files if it doesn't exist
VOICE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_files")
os.makedirs(VOICE_DIR, exist_ok=True)

# Initialize Kokoro TTS with fallback
tts = None
try:
    # Import Kokoro only if available
    import torch
    from kokoro import KPipeline, load_tts_model, TTSConfig
    
    # 'a' for American English - this is the correct code format for Kokoro
    tts = KPipeline(lang_code='a')
    logger.info("Kokoro TTS initialized successfully")
    
    # Map of voice IDs to filenames and HuggingFace paths
    VOICE_MAPPINGS = {
        "default": {"file": "af_heart.pt", "huggingface": "af_heart"},
        "female1": {"file": "af_sarah.pt", "huggingface": "af_sarah"},
        "female2": {"file": "af_nicole.pt", "huggingface": "af_nicole"},
        "male1": {"file": "am_michael.pt", "huggingface": "am_michael"},
        "male2": {"file": "am_adam.pt", "huggingface": "am_adam"},
        "british": {"file": "bf_isabella.pt", "huggingface": "bf_isabella"},
        "australian": {"file": "bf_emma.pt", "huggingface": "bf_emma"}
    }
except Exception as e:
    logger.error(f"Error initializing Kokoro TTS: {e}")
    logger.info("TTS functionality will be limited to text-only responses")

def download_voice_file(voice_id):
    """Download voice file from HuggingFace if it doesn't exist locally."""
    if tts is None:
        logger.warning("Kokoro not initialized, can't download voice files")
        return False
        
    try:
        voice_info = VOICE_MAPPINGS.get(voice_id, VOICE_MAPPINGS["default"])
        voice_file = voice_info["file"]
        huggingface_id = voice_info["huggingface"]
        
        voice_path = os.path.join(VOICE_DIR, voice_file)
        
        # If the file already exists, return success
        if os.path.exists(voice_path):
            logger.info(f"Voice file {voice_file} already exists")
            return True
            
        # Try to download the voice file from HuggingFace
        logger.info(f"Downloading voice file {voice_file} from HuggingFace...")
        
        # Construct the correct HuggingFace URL with the proper voice ID
        # The URL format should be 'resolve/main/' not 'blob/main/'
        url = f"https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices/{huggingface_id}.pt"
        logger.info(f"Download URL: {url}")
        
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(voice_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Successfully downloaded voice file {voice_file}")
            return True
        else:
            logger.error(f"Failed to download voice file: HTTP {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error downloading voice file: {e}")
        return False

def get_voice_file(voice_id):
    """Get the path to a voice file, downloading it if needed."""
    if tts is None:
        logger.error("Kokoro TTS not initialized")
        return None

    # If voice_id is not found in mappings, use default
    if voice_id not in VOICE_MAPPINGS:
        logger.warning(f"Voice ID '{voice_id}' not found, using default")
        voice_id = "default"

    voice_info = VOICE_MAPPINGS[voice_id]
    voice_file = voice_info["file"]
    voice_path = os.path.join(VOICE_DIR, voice_file)

    # If the file doesn't exist, try to download it
    if not os.path.exists(voice_path):
        logger.info(f"Voice file {voice_file} not found, attempting to download")
        success = download_voice_file(voice_id)
        if not success:
            logger.error(f"Failed to download voice file for {voice_id}")
            return None

    # Return the path if it exists now
    if os.path.exists(voice_path):
        return voice_path
    else:
        return None

def list_available_voices():
    """Return a list of available voice IDs."""
    if tts is None:
        return []
    
    available_voices = []
    for voice_id in VOICE_MAPPINGS:
        voice_file = VOICE_MAPPINGS[voice_id]["file"]
        voice_path = os.path.join(VOICE_DIR, voice_file)
        if os.path.exists(voice_path):
            available_voices.append(voice_id)
    
    return available_voices

def text_to_speech(text, voice_option='default'):
    """Convert text to speech using Kokoro TTS."""
    import base64
    import os
    import logging
    import re
    import numpy as np

    try:
        MAX_TEXT_LENGTH = 500  # Maximum characters per chunk
        
        # Handle long text by splitting into chunks at sentence boundaries
        if len(text) > MAX_TEXT_LENGTH:
            logging.info(f"Text length ({len(text)}) exceeds maximum ({MAX_TEXT_LENGTH}). Splitting into chunks.")
            
            # Split at sentence boundaries (periods, question marks, exclamation points followed by space)
            sentence_pattern = r'[.!?]\s+'
            sentences = re.split(sentence_pattern, text)
            
            # Rebuild sentences with their punctuation
            chunks = []
            current_chunk = ""
            
            for i, sentence in enumerate(sentences):
                # Skip empty sentences
                if not sentence.strip():
                    continue
                
                # Add punctuation back if this isn't the last sentence
                if i < len(sentences) - 1:
                    # Find which punctuation was used
                    match_pos = text.find(sentence) + len(sentence)
                    if match_pos < len(text):
                        punct = text[match_pos]
                        sentence = sentence + punct + " "
                
                # Check if adding this sentence would exceed our chunk size
                if len(current_chunk) + len(sentence) <= MAX_TEXT_LENGTH:
                    current_chunk += sentence
                else:
                    # If the current chunk is not empty, save it and start a new one
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
            
            # Add the final chunk if not empty
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            logging.info(f"Split text into {len(chunks)} chunks")
            
            # For now, just process the first chunk to avoid huge audio files
            # In a more advanced implementation, you could process all chunks
            text = chunks[0]
            is_truncated = len(chunks) > 1
            total_chunks = len(chunks)
        else:
            is_truncated = False
            total_chunks = 1
        
        logging.info(f"Processing text for TTS: {text[:50]}... ({len(text)} chars)")
        
        # Select voice model based on voice_option
        voice_file = get_voice_file(voice_option)
        if not voice_file:
            logging.error(f"No voice file found for {voice_option}, falling back to browser TTS")
            return None, {
                "error": f"Voice '{voice_option}' not available",
                "available_voices": list_available_voices()
            }
        
        logging.info(f"Using voice file: {voice_file}")
        
        # Initialize Kokoro TTS
        from kokoro import load_tts_model, TTSConfig
        
        # Load the model with lower sample rate for smaller file size
        tts_config = TTSConfig()
        tts_config.sample_rate = 16000  # Lower sample rate (was 22050) for smaller files
        
        try:
            model = load_tts_model(voice_file, tts_config)
        except Exception as e:
            logging.error(f"Failed to load TTS model: {e}")
            return None, {"error": f"Failed to load TTS model: {str(e)}"}
        
        # Generate audio
        try:
            audio_array = model.tts(text)
            
            # Create a WAV file in memory
            try:
                # Use scipy.io.wavfile if available for better handling
                try:
                    from scipy.io import wavfile
                    import io
                    
                    wav_buffer = io.BytesIO()
                    wavfile.write(wav_buffer, tts_config.sample_rate, audio_array)
                    wav_buffer.seek(0)
                    wav_data = wav_buffer.read()
                except ImportError:
                    # Fallback to manual WAV creation
                    logging.info("scipy.io.wavfile not available, creating WAV file manually")
                    wav_data = create_wav_file(audio_array, tts_config.sample_rate)
                
                # Convert to base64
                audio_base64 = base64.b64encode(wav_data).decode('utf-8')
                
                # Check if compression would help
                try:
                    import zlib
                    compressed_data = zlib.compress(wav_data, level=9)
                    compression_ratio = len(compressed_data) / len(wav_data)
                    
                    # If compression saves at least 20% space, use it
                    if compression_ratio <= 0.8:
                        logging.info(f"Compressing audio data, ratio: {compression_ratio:.2f}")
                        compressed_base64 = base64.b64encode(compressed_data).decode('utf-8')
                        
                        # Return audio data and metadata
                        return compressed_base64, {
                            "is_compressed": True,
                            "sample_rate": tts_config.sample_rate,
                            "original_size": len(wav_data),
                            "compressed_size": len(compressed_data),
                            "text_length": len(text),
                            "truncated": is_truncated,
                            "total_chunks": total_chunks
                        }
                    else:
                        logging.info(f"Compression not effective (ratio: {compression_ratio:.2f}), skipping")
                except ImportError:
                    logging.info("zlib not available, skipping compression")
                
                # Return uncompressed audio data and metadata
                return audio_base64, {
                    "is_compressed": False,
                    "sample_rate": tts_config.sample_rate,
                    "original_size": len(wav_data),
                    "text_length": len(text),
                    "truncated": is_truncated,
                    "total_chunks": total_chunks
                }
            except Exception as wav_error:
                logging.error(f"Failed to create WAV file: {wav_error}")
                return None, {"error": f"Failed to create WAV file: {str(wav_error)}"}
                
        except Exception as tts_error:
            logging.error(f"Failed to generate TTS: {tts_error}")
            return None, {"error": f"Failed to generate TTS: {str(tts_error)}"}
    except Exception as e:
        logging.error(f"Unexpected error in text_to_speech: {e}")
        return None, {"error": f"Unexpected error: {str(e)}"}

def create_wav_file(audio_array, sample_rate):
    """Create a WAV file from a numpy array."""
    import struct
    
    # Normalize audio to 16-bit range
    audio_max = np.max(np.abs(audio_array))
    if audio_max > 0:
        audio_array = audio_array * 32767 / audio_max
    
    # Convert to 16-bit integer
    audio_array = audio_array.astype(np.int16)
    
    # Create WAV header
    header = bytearray()
    
    # RIFF header
    header.extend(b'RIFF')
    header.extend(struct.pack('<I', 36 + len(audio_array) * 2))  # File size
    header.extend(b'WAVE')
    
    # Format chunk
    header.extend(b'fmt ')
    header.extend(struct.pack('<I', 16))  # Chunk size
    header.extend(struct.pack('<H', 1))   # Format = PCM
    header.extend(struct.pack('<H', 1))   # Channels = 1 (mono)
    header.extend(struct.pack('<I', sample_rate))  # Sample rate
    header.extend(struct.pack('<I', sample_rate * 2))  # Byte rate (sample rate * block align)
    header.extend(struct.pack('<H', 2))   # Block align
    header.extend(struct.pack('<H', 16))  # Bits per sample
    
    # Data chunk
    header.extend(b'data')
    header.extend(struct.pack('<I', len(audio_array) * 2))  # Chunk size
    
    # Combine header and audio data
    wav_data = bytearray(header)
    wav_data.extend(audio_array.tobytes())
    
    return bytes(wav_data)

class handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        """Set headers for CORS."""
        origin = self.headers.get('Origin', '*')
        self.send_header('Access-Control-Allow-Origin', origin)
        self.send_header('Access-Control-Allow-Methods', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Credentials', 'true')
    
    def do_OPTIONS(self):
        """Handle preflight CORS requests."""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        # Check if requesting a voice file (for debugging)
        if self.path.startswith("/api/voices/"):
            voice_id = self.path.split("/")[-1]
            if voice_id in VOICE_MAPPINGS:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                
                voice_path = os.path.join(VOICE_DIR, VOICE_MAPPINGS[voice_id]["file"])
                exists = os.path.exists(voice_path)
                
                self.wfile.write(json.dumps({
                    "voice_id": voice_id,
                    "file": VOICE_MAPPINGS[voice_id]["file"],
                    "exists": exists,
                    "path": voice_path
                }).encode())
                return
        
        # Handle /api/debug endpoint
        if self.path.startswith("/api/debug"):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            
            # Get requester's IP address
            client_address = self.headers.get('X-Forwarded-For', self.client_address[0])
            logger.info(f"Debug request received from: {client_address}")
            
            # Prepare debug info
            debug_info = {
                "status": "API is running",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "kokoro_available": tts is not None,
                "voices_dir": VOICE_DIR,
                "available_voices": list(VOICE_MAPPINGS.keys()) if tts else []
            }
            
            # Add voice file information if Kokoro is available
            if tts:
                voice_files = {}
                for voice_id, info in VOICE_MAPPINGS.items():
                    voice_path = os.path.join(VOICE_DIR, info["file"])
                    voice_files[voice_id] = {
                        "file": info["file"],
                        "exists": os.path.exists(voice_path)
                    }
                debug_info["voice_files"] = voice_files
            
            self.wfile.write(json.dumps(debug_info).encode())
            return
            
        # Default GET response for API
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"status": "API is running"}).encode())
    
    def do_POST(self):
        """Handle POST requests."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # Parse content type
        content_type = self.headers.get('Content-Type', '')
        
        # Set response headers
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        
        # Process the request based on the path
        if self.path.startswith("/api/text"):
            self._handle_text_request(post_data)
        elif self.path.startswith("/api/voice"):
            self._handle_voice_request(post_data, content_type)
        else:
            # Default response for unknown endpoints
            self.wfile.write(json.dumps({
                "error": "Unknown endpoint"
            }).encode())
    
    def _handle_text_request(self, post_data):
        """Handle text generation requests."""
        try:
            request_json = json.loads(post_data)
            user_input = request_json.get('text', '')
            
            if not user_input:
                self.wfile.write(json.dumps({
                    "error": "No text provided"
                }).encode())
                return
            
            # Generate AI response
            prompt = f"User: {user_input}\nAssistant: "
            response = model.generate_content(prompt)
            
            self.wfile.write(json.dumps({
                "response": response.text
            }).encode())
        except json.JSONDecodeError:
            self.wfile.write(json.dumps({
                "error": "Invalid JSON"
            }).encode())
        except Exception as e:
            logger.error(f"Error processing text request: {e}")
            self.wfile.write(json.dumps({
                "error": str(e)
            }).encode())
    
    def _handle_voice_request(self, post_data, content_type):
        """Handle voice generation requests."""
        try:
            # Parse JSON data from request
            if 'application/json' in content_type:
                try:
                    request_json = json.loads(post_data)
                except json.JSONDecodeError:
                    self.wfile.write(json.dumps({
                        "error": "Invalid JSON in request"
                    }).encode('utf-8'))
                    return
            else:
                self.wfile.write(json.dumps({
                    "error": "Content-Type must be application/json"
                }).encode('utf-8'))
                return
            
            text = request_json.get('text', '')
            voice = request_json.get('voice', 'default')
            
            if not text:
                self.wfile.write(json.dumps({
                    "error": "No text provided"
                }).encode('utf-8'))
                return
            
            # Generate AI response first if text is a question
            if text.strip().endswith('?') or len(text.split()) < 10:
                prompt = f"User: {text}\nAssistant: "
                try:
                    ai_response = model.generate_content(prompt)
                    text = ai_response.text
                    logger.info(f"Generated voice response: {text}")
                except Exception as ai_error:
                    logger.error(f"Error generating AI response: {ai_error}")
                    # Continue with the original text if AI generation fails
            
            # Generate audio using Kokoro - with detailed logging
            response_data = {"response": text}
            
            try:
                logger.info(f"Processing chunk 1/1, length: {len(text)}")
                logger.info(f"Generating voice for text using voice: {voice}")
                logger.info(f"Selected Kokoro voice ID: {voice}")
                logger.info(f"Calling Kokoro pipeline with text length: {len(text)}")
                logger.info(f"Text preview: {text[:50]}...")
                
                # Generate audio
                audio_data, metadata = text_to_speech(text, voice)
                
                if audio_data:
                    # Ensure audio_data is properly encoded as base64 string
                    if isinstance(audio_data, bytes):
                        audio_data = base64.b64encode(audio_data).decode('utf-8')
                    
                    response_data["audio"] = audio_data
                    response_data["metadata"] = metadata
                    
                    # Log success information
                    kb_size = len(audio_data) // 1000
                    logger.info(f"Generated audio response ({kb_size}KB)")
                    logger.info(f"Generated {metadata.get('total_chunks', 1)} audio chunks")
                else:
                    # Handle case where no audio data was returned
                    if isinstance(metadata, dict) and "error" in metadata:
                        error_message = metadata["error"]
                        logger.error(f"TTS error: {error_message}")
                        response_data["error"] = error_message
                    else:
                        logger.error("Failed to generate audio: No audio data returned")
                        response_data["error"] = "Failed to generate audio"
                    
                    # Include helpful debugging information
                    response_data["fallback"] = True
                    response_data["status"] = "partial_success"
                    response_data["message"] = "Text generated successfully, but audio generation failed."
            except Exception as tts_error:
                # Log the full traceback for debugging
                logger.error(f"TTS error: {tts_error}")
                logger.error(f"TTS traceback: {traceback.format_exc()}")
                
                response_data["error"] = str(tts_error)
                response_data["fallback"] = True
                response_data["status"] = "partial_success"
                response_data["message"] = "Text generated successfully, but audio generation failed due to an error."
            
            # Serialize to JSON and ensure UTF-8 encoding for non-binary data
            try:
                response_json = json.dumps(response_data)
                self.wfile.write(response_json.encode('utf-8'))
            except TypeError as json_error:
                # Handle case where response data contains non-serializable objects
                logger.error(f"JSON serialization error: {json_error}")
                error_response = {
                    "error": f"Failed to serialize response: {str(json_error)}",
                    "response": text
                }
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
            
        except Exception as e:
            # Generic error handler
            logger.error(f"Error processing voice request: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            error_response = {
                "error": str(e),
                "response": "Sorry, there was an error processing your request."
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

# For direct testing outside of Vercel
def test(event, context):
    path = event.get('path', '')
    method = event.get('httpMethod', 'GET')
    headers = event.get('headers', {})
    body = event.get('body', '{}')
    
    if method == 'OPTIONS':
        return generate_response(200, {"status": "ok"})
    
    if method == 'GET':
        return generate_response(200, {
            "status": "ok",
            "message": "Interview AI API is running",
            "path": path,
            "method": method
        })
    
    if method == 'POST':
        try:
            request_data = json.loads(body)
            user_text = request_data.get('text', '')
            voice = request_data.get('voice', 'default')
        except:
            user_text = "Error parsing JSON"
            voice = 'default'
        
        if "/api/text" in path:
            return generate_response(200, {
                "response": f"API response for: {user_text}",
                "endpoint": "text"
            })
        elif "/api/voice" in path:
            response_text = f"Voice response for: {user_text}"
            audio_base64, error, fallback_info = text_to_speech(response_text, voice=voice)
            
            response_data = {
                "status": "success" if audio_base64 else "partial_success",
                "response": response_text
            }
            
            if audio_base64:
                response_data["audio"] = audio_base64
            
            # Include fallback info if available
            if fallback_info:
                response_data.update(fallback_info)
            elif error:
                response_data["error"] = error
                response_data["fallback"] = True
            
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Expose-Headers": "X-Response-Text",
                    "X-Response-Text": response_text
                },
                "body": json.dumps(response_data)
            }
        else:
            return generate_response(404, {
                "response": f"Unknown endpoint: {path}",
                "endpoint": "unknown"
            })
    
    return generate_response(405, {"error": "Method not allowed"})

def generate_response(status_code, body):
    """Helper function to generate API responses."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
        },
        "body": json.dumps(body)
    } 