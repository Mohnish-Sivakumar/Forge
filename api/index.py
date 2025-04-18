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
import urllib.request
import glob

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

# Define primary voice model to use - this will be downloaded first
PRIMARY_VOICE_ID = "af_heart"

# Define limited voice options to save space
ESSENTIAL_VOICES = {
    "default": "af_heart",  # Default female voice
    "female1": "af_heart",  # Default female voice - reused
    "male1": "am_michael",  # Male voice option
    "male2": "am_adam",     # Alternative male voice
}

# Map friendly names to actual voice IDs
VOICE_MAP = {
    "default": "af_heart",
    "female1": "af_heart",
    "female2": "af_bella",
    "male1": "am_michael",
    "male2": "am_adam",
    "british": "en_joylin",
    "australian": "en_william"
}

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
    """Download a specific voice file from HuggingFace"""
    
    # Create voice_files directory if it doesn't exist
    os.makedirs('voice_files', exist_ok=True)
    
    # Destination path for the voice file
    dest_path = os.path.join('voice_files', f'{voice_id}.pt')
    
    # If file already exists and has content, skip download
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        print(f"Voice file {voice_id}.pt already exists")
        return True

    try:
        # URL for the voice file on HuggingFace
        url = f"https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices/{voice_id}.pt"
        
        # Create a request with a timeout
        req = urllib.request.Request(url)
        
        # Try to download the file
        with urllib.request.urlopen(req, timeout=20) as response:
            # Write the file in chunks to avoid memory issues
            with open(dest_path, 'wb') as f:
                chunk_size = 1024 * 1024  # 1MB chunks
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    f.flush()  # Ensure data is written to disk
            
            print(f"Downloaded voice file {voice_id}.pt")
            return True
    except Exception as e:
        print(f"Error downloading voice file {voice_id}.pt: {str(e)}")
        # Remove partial file if download failed
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except:
                pass
        return False

def get_voice_file(voice_option='default'):
    """Get the path to a voice file, downloading it if necessary"""
    
    # Map the voice option to a voice ID
    voice_id = VOICE_MAP.get(voice_option, "af_heart")
    
    # Check if we're limiting to essential voices only
    if os.environ.get('ESSENTIAL_VOICES_ONLY', 'true').lower() == 'true':
        # Use only essential voices to save space
        voice_id = ESSENTIAL_VOICES.get(voice_option, PRIMARY_VOICE_ID)
    
    # Create voice_files directory if it doesn't exist
    os.makedirs('voice_files', exist_ok=True)
    
    # Path to the voice file
    voice_file_path = os.path.join('voice_files', f'{voice_id}.pt')
    
    # If file doesn't exist or is empty, try to download it
    if not os.path.exists(voice_file_path) or os.path.getsize(voice_file_path) == 0:
        success = download_voice_file(voice_id)
        
        # If download failed, try to use the primary voice instead
        if not success and voice_id != PRIMARY_VOICE_ID:
            print(f"Falling back to primary voice {PRIMARY_VOICE_ID}")
            voice_id = PRIMARY_VOICE_ID
            voice_file_path = os.path.join('voice_files', f'{voice_id}.pt')
            
            # Try to download the primary voice if needed
            if not os.path.exists(voice_file_path) or os.path.getsize(voice_file_path) == 0:
                download_voice_file(voice_id)
    
    # Return the path to the voice file if it exists
    if os.path.exists(voice_file_path) and os.path.getsize(voice_file_path) > 0:
        return voice_file_path
    
    # If we couldn't get a voice file, return None
    return None

def list_available_voices():
    """List available voice files"""
    voice_files = []
    try:
        # Create voice_files directory if it doesn't exist
        os.makedirs('voice_files', exist_ok=True)
        
        # List files in the directory
        for file in os.listdir('voice_files'):
            if file.endswith('.pt') and os.path.getsize(os.path.join('voice_files', file)) > 0:
                voice_id = file.replace('.pt', '')
                voice_files.append(voice_id)
    except Exception as e:
        print(f"Error listing voice files: {str(e)}")
    
    return voice_files

def text_to_speech(text, voice_option='default'):
    """Convert text to speech using Kokoro TTS"""
    
    # Clean up any temporary files from previous runs
    for temp_file in glob.glob('temp_*.wav'):
        try:
            os.remove(temp_file)
        except:
            pass
    
    # Check if Kokoro is available
    try:
        import kokoro
    except ImportError:
        print("Kokoro TTS not available")
        return None
    
    # Get the voice file path
    voice_path = get_voice_file(voice_option)
    
    # If voice file not available, return None
    if not voice_path:
        print(f"Voice file for {voice_option} not available")
        return None
    
    try:
        # Create Kokoro pipeline
        tts_pipeline = kokoro.T2SModel(voice_path)
        
        # Set parameters for better quality
        voice_samples, sampling_rate = tts_pipeline.inference(
            text,
            top_k=30,
            top_p=0.5,
            temperature=0.7
        )
        
        # Convert PyTorch tensor to numpy array
        audio_array = voice_samples.cpu().numpy()
        
        # Create WAV file from the audio data
        return create_wav_file(audio_array, sampling_rate)
    except Exception as e:
        print(f"Error in text-to-speech: {str(e)}")
        return None
    finally:
        # Clean up to free memory
        if 'tts_pipeline' in locals():
            del tts_pipeline
        import gc
        gc.collect()
        
        # Try to free up CUDA memory if available
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except:
            pass

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

# Function to clean up unused voice files
def cleanup_voice_files():
    """Remove unused voice files to save space, keeping only essential voices"""
    try:
        # Create voice_files directory if it doesn't exist
        voice_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_files")
        os.makedirs(voice_dir, exist_ok=True)
        
        # Always keep these essential voice files
        essential_files = set([f"{ESSENTIAL_VOICES[k]}.pt" for k in ESSENTIAL_VOICES])
        
        # Also always keep the primary voice
        essential_files.add(f"{PRIMARY_VOICE_ID}.pt")
        
        # Get the current timestamp
        now = time.time()
        
        # List all voice files
        for file in os.listdir(voice_dir):
            if file.endswith('.pt') and file not in essential_files:
                file_path = os.path.join(voice_dir, file)
                
                # Get the file's last access time
                file_atime = os.path.getatime(file_path)
                
                # If the file hasn't been accessed in the last 30 days, delete it
                if now - file_atime > 30 * 24 * 60 * 60:  # 30 days in seconds
                    try:
                        os.remove(file_path)
                        print(f"Removed unused voice file: {file}")
                    except Exception as e:
                        print(f"Error removing voice file {file}: {str(e)}")
    except Exception as e:
        print(f"Error cleaning up voice files: {str(e)}")

# Also clean up other temp files
def cleanup_temp_files():
    """Remove temporary files to save space"""
    try:
        # Clean up any temporary WAV files
        for temp_file in glob.glob('temp_*.wav'):
            try:
                # Check if the file is older than 1 hour
                file_mtime = os.path.getmtime(temp_file)
                if time.time() - file_mtime > 60 * 60:  # 1 hour in seconds
                    os.remove(temp_file)
                    print(f"Removed old temp file: {temp_file}")
            except:
                pass
    except Exception as e:
        print(f"Error cleaning up temp files: {str(e)}")

# Call cleanup functions periodically
cleanup_counter = 0

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
        global cleanup_counter
        
        # Run cleanup every 50 requests
        cleanup_counter += 1
        if cleanup_counter >= 50:
            cleanup_counter = 0
            cleanup_temp_files()
            
            # Only run voice cleanup occasionally (every 100 requests)
            if cleanup_counter % 2 == 0:
                cleanup_voice_files()
                
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