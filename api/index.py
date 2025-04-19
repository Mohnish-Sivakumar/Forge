import json
import os
import sys
import traceback
import logging
from http.server import BaseHTTPRequestHandler
import google.generativeai as genai
import gc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure API key
api_key = os.environ.get("GEMINI_API_KEY", "your-api-key")
genai.configure(api_key=api_key)

# Set up a memory saving mode flag
MEMORY_SAVING_MODE = True  # Set to True to use memory optimization techniques
MAX_MEMORY_USAGE = 400  # Maximum memory in MB to use

# Setup Gemini model
model = genai.GenerativeModel("gemini-pro")

# Global variable to hold loaded Kokoro instances (lazy loaded)
kokoro_instance = None

# Add this global variable section with other globals
_kokoro_loaded = False
_MEMORY_LIMIT = float(os.environ.get('MAX_MEMORY_MB', 400)) * 0.8  # 80% of max memory
_CACHE_VOICES = {}  # Voice model cache

def lazy_load_kokoro(force=False):
    """Load Kokoro only when needed and if memory allows"""
    global _kokoro_loaded
    
    # Skip if already loaded and not forced
    if _kokoro_loaded and not force:
        return True
    
    # Check memory availability before loading
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"Current memory usage before loading Kokoro: {memory_mb:.2f} MB")
        
        # Only load if we have enough memory headroom
        if memory_mb > _MEMORY_LIMIT * 0.7:  # If using more than 70% of memory limit
            print(f"WARNING: Memory usage too high to load Kokoro: {memory_mb:.2f} MB > {_MEMORY_LIMIT * 0.7:.2f} MB")
            return False
    except ImportError:
        print("Cannot check memory usage - proceeding with caution")
    
    # Try to import Kokoro with CPU-only settings
    try:
        # Set environment variables to force CPU mode
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        os.environ['TORCH_CPU_MODE'] = '1'
        
        # Import libraries directly here to keep them out of memory when not needed
        import torch
        torch.set_num_threads(2)  # Limit thread count to save memory
        
        # Now import Kokoro with minimal voice options
        import kokoro
        global tts_pipe, voices
        
        # Setup Kokoro with minimal settings
        tts_pipe = kokoro.Pipeline()
        voices = {
            'default': 'af_heart',      # Default female voice
            'female1': 'af_heart',      # Female voice
            'male1': 'am_michael'       # Male voice
        }
        _kokoro_loaded = True
        print("Successfully loaded Kokoro")
        return True
        
    except Exception as e:
        print(f"Failed to load Kokoro: {e}")
        return False

def cleanup_kokoro():
    """Clean up Kokoro resources to free memory"""
    global _kokoro_loaded, tts_pipe, _CACHE_VOICES
    
    if _kokoro_loaded:
        try:
            # Clear Kokoro pipeline
            tts_pipe = None
            _CACHE_VOICES = {}
            
            # Clear Torch cache if possible
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except:
                pass
                
            # Force garbage collection
            gc.collect()
            _kokoro_loaded = False
            print("Kokoro resources released")
        except Exception as e:
            print(f"Error during Kokoro cleanup: {e}")

def text_to_speech(text, voice_option='default'):
    """Generate speech audio from text using the specified voice"""
    if not text:
        return None, "Empty text provided"
    
    # Load Kokoro if needed
    if not lazy_load_kokoro():
        return None, "Insufficient memory to load voice model"
    
    try:
        # Select voice ID
        voice_id = voices.get(voice_option, 'af_heart')
        print(f"Selected Kokoro voice ID: {voice_id}")
        
        # Generate audio
        print(f"Calling Kokoro pipeline with text length: {len(text)}")
        print(f"Text preview: {text[:50]}...")
        
        # Generate speech
        audio = tts_pipe.generate_speech(text, voice_id)
        
        # Clean up to free memory
        cleanup_kokoro()
        gc.collect()
        
        return audio, None
        
    except Exception as e:
        import traceback
        print(f"Error generating speech: {e}")
        print(traceback.format_exc())
        cleanup_kokoro()
        return None, str(e)

def list_available_voices():
    """List available voice options"""
    voices = ["default", "male1", "male2"]
    
    # Check if Kokoro is available
    if lazy_load_kokoro() is not None:
        return {
            "voices": voices,
            "kokoro_available": True
        }
    else:
        return {
            "voices": voices,
            "kokoro_available": False,
            "message": "Running in low-memory mode. Voice synthesis may use browser TTS as fallback."
        }

class handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Expose-Headers", "X-Response-Text")
        self.send_header("Access-Control-Allow-Credentials", "true")

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        try:
            path = self.path.strip('/')
            
            # Handle root path
            if path == "api" or path == "api/":
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                response = {
                    "status": "ok",
                    "message": "Interview AI API running",
                    "memory_saving_mode": MEMORY_SAVING_MODE
                }
                self.wfile.write(json.dumps(response).encode())
                return
                
            # Handle debug info
            if path == "api/debug":
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                
                # Check memory usage
                memory_info = {"available": False}
                try:
                    import psutil
                    process = psutil.Process(os.getpid())
                    mem_info = process.memory_info()
                    memory_info = {
                        "available": True,
                        "rss_mb": mem_info.rss / 1024 / 1024,
                        "vms_mb": mem_info.vms / 1024 / 1024,
                        "limit_mb": MAX_MEMORY_USAGE
                    }
                except ImportError:
                    pass
                
                response = {
                    "status": "ok",
                    "api_version": "1.0.0",
                    "python_version": sys.version,
                    "memory_saving_mode": MEMORY_SAVING_MODE,
                    "memory": memory_info,
                    "available_voices": list_available_voices(),
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Handle voice info
            if path == "api/voices":
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                
                response = list_available_voices()
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Handle memory check
            if path == "api/memory":
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                
                try:
                    import psutil
                    process = psutil.Process(os.getpid())
                    mem_info = process.memory_info()
                    response = {
                        "status": "ok",
                        "memory_mb": mem_info.rss / 1024 / 1024,
                        "limit_mb": MAX_MEMORY_USAGE,
                        "within_limit": (mem_info.rss / 1024 / 1024) < MAX_MEMORY_USAGE
                    }
                except ImportError:
                    response = {
                        "status": "error",
                        "message": "psutil not available, cannot check memory"
                    }
                
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Handle other GET requests
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            response = {"error": "Not found", "path": path}
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            response = {"error": str(e), "traceback": traceback.format_exc()}
            self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            path = self.path.strip('/')
            
            # Parse JSON data if content exists
            if content_length > 0:
                try:
                    post_data = json.loads(post_data)
                except json.JSONDecodeError:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self._set_cors_headers()
                    self.end_headers()
                    response = {"error": "Invalid JSON data"}
                    self.wfile.write(json.dumps(response).encode())
                    return
            else:
                post_data = {}
            
            # Handle text endpoint
            if path == "api/text":
                self._handle_text_request(post_data)
                return
                
            # Handle voice endpoint
            if path == "api/voice":
                self._handle_voice_request(post_data)
                return
                
            # Handle login endpoint
            if path == "api/login":
                # Simple test login, always returns success
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                
                username = post_data.get('username', '')
                response = {
                    "status": "success", 
                    "message": f"Welcome, {username}!",
                    "user": {"username": username, "role": "user"}
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Handle unknown endpoints
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            response = {"error": "Endpoint not found", "path": path}
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            response = {"error": str(e)}
            self.wfile.write(json.dumps(response).encode())

    def _handle_text_request(self, post_data):
        # Extract text from POST data
        text = post_data.get('text', '')
        if not text:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            response = {"error": "No text provided"}
            self.wfile.write(json.dumps(response).encode())
            return

        try:
            # Generate response using AI
            ai_response = model.generate_content(
                f"You are an interview coach called Interview AI. Keep your response concise. Question: {text}"
            )
            ai_text = ai_response.text
            
            # Log the generated response
            logger.info(f"Generated text response: {ai_text[:100]}...")
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('X-Response-Text', ai_text[:100]) # For easier debugging
            self._set_cors_headers()
            self.end_headers()
            
            response = {"status": "success", "response": ai_text}
            self.wfile.write(json.dumps(response).encode())
        
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            response = {"error": str(e), "details": traceback.format_exc()}
            self.wfile.write(json.dumps(response).encode())

    def _handle_voice_request(self, post_data):
        # Extract text from POST data
        text = post_data.get('text', '')
        voice = post_data.get('voice', 'default')
        
        if not text:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            response = {"error": "No text provided"}
            self.wfile.write(json.dumps(response).encode())
            return

        try:
            # Generate response using AI
            ai_response = model.generate_content(
                f"You are an interview coach called Interview AI. Keep your response concise. Question: {text}"
            )
            ai_text = ai_response.text
            
            # Log the generated response
            logger.info(f"Generated voice response: {ai_text[:100]}...")
            
            # Check memory before attempting voice synthesis
            can_use_kokoro = True
            try:
                import psutil
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                
                if memory_mb > MAX_MEMORY_USAGE:
                    logger.warning(f"Memory usage ({memory_mb:.2f} MB) exceeds limit ({MAX_MEMORY_USAGE} MB). Using text-only mode.")
                    can_use_kokoro = False
            except ImportError:
                logger.warning("psutil not available, assuming memory is available")
            
            if can_use_kokoro:
                # Try to generate speech
                tts_result, error = text_to_speech(ai_text, voice)
                
                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Response-Text', ai_text[:100]) # For easier debugging
                self._set_cors_headers()
                self.end_headers()
                
                response = {
                    "status": "success", 
                    "response": ai_text,
                    "text": ai_text
                }
                
                # Add audio data if available
                if tts_result:
                    response["audio"] = tts_result
                    response["format"] = "base64"
                    response["voice"] = voice
                else:
                    # No audio, return text only with a message
                    response["low_memory_mode"] = True
                    response["message"] = error
                
                self.wfile.write(json.dumps(response).encode())
            else:
                # Memory limit reached, return text-only response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('X-Response-Text', ai_text[:100]) # For easier debugging
                self._set_cors_headers()
                self.end_headers()
                
                response = {
                    "status": "success", 
                    "response": ai_text,
                    "text": ai_text,
                    "low_memory_mode": True,
                    "message": "Running in low-memory mode. Voice synthesis will happen in the browser."
                }
                self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            response = {"error": str(e), "details": traceback.format_exc()}
            self.wfile.write(json.dumps(response).encode())

def test(event, context):
    """Handler for AWS Lambda or similar serverless environments"""
    path = event.get("path", "")
    http_method = event.get("httpMethod", "GET")
    headers = event.get("headers", {})
    query_params = event.get("queryStringParameters", {})
    body = event.get("body", "")
    
    if isinstance(body, str) and body:
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            return generate_response(400, {"error": "Invalid JSON in request body"})
    
    # Handle OPTIONS requests for CORS
    if http_method == "OPTIONS":
        return generate_response(
            200, 
            {}, 
            {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Expose-Headers": "X-Response-Text",
                "Access-Control-Allow-Credentials": "true"
            }
        )
    
    # Handle GET requests
    if http_method == "GET":
        if path == "/api" or path == "/api/":
            return generate_response(200, {
                "status": "ok",
                "message": "Interview AI API running",
                "memory_saving_mode": MEMORY_SAVING_MODE
            })
        
        if path == "/api/debug":
            # Check memory usage
            memory_info = {"available": False}
            try:
                import psutil
                process = psutil.Process(os.getpid())
                mem_info = process.memory_info()
                memory_info = {
                    "available": True,
                    "rss_mb": mem_info.rss / 1024 / 1024,
                    "vms_mb": mem_info.vms / 1024 / 1024,
                    "limit_mb": MAX_MEMORY_USAGE
                }
            except ImportError:
                pass
                
            return generate_response(200, {
                "status": "ok",
                "api_version": "1.0.0",
                "python_version": sys.version,
                "memory_saving_mode": MEMORY_SAVING_MODE,
                "memory": memory_info,
                "available_voices": list_available_voices(),
            })
        
        if path == "/api/voices":
            return generate_response(200, list_available_voices())
        
        if path == "/api/memory":
            try:
                import psutil
                process = psutil.Process(os.getpid())
                mem_info = process.memory_info()
                response = {
                    "status": "ok",
                    "memory_mb": mem_info.rss / 1024 / 1024,
                    "limit_mb": MAX_MEMORY_USAGE,
                    "within_limit": (mem_info.rss / 1024 / 1024) < MAX_MEMORY_USAGE
                }
            except ImportError:
                response = {
                    "status": "error",
                    "message": "psutil not available, cannot check memory"
                }
            
            return generate_response(200, response)
        
        return generate_response(404, {"error": "Not found", "path": path})
    
    # Handle POST requests
    if http_method == "POST":
        if path == "/api/text":
            text = body.get("text", "") if isinstance(body, dict) else ""
            if not text:
                return generate_response(400, {"error": "No text provided"})
            
            try:
                ai_response = model.generate_content(
                    f"You are an interview coach called Interview AI. Keep your response concise. Question: {text}"
                )
                ai_text = ai_response.text
                
                logger.info(f"Generated text response: {ai_text[:100]}...")
                
                return generate_response(
                    200, 
                    {"status": "success", "response": ai_text},
                    {"X-Response-Text": ai_text[:100]}
                )
            except Exception as e:
                return generate_response(500, {"error": str(e), "details": traceback.format_exc()})
        
        if path == "/api/voice":
            text = body.get("text", "") if isinstance(body, dict) else ""
            voice = body.get("voice", "default") if isinstance(body, dict) else "default"
            
            if not text:
                return generate_response(400, {"error": "No text provided"})
            
            try:
                ai_response = model.generate_content(
                    f"You are an interview coach called Interview AI. Keep your response concise. Question: {text}"
                )
                ai_text = ai_response.text
                
                logger.info(f"Generated voice response: {ai_text[:100]}...")
                
                # Check memory before attempting voice synthesis
                can_use_kokoro = True
                try:
                    import psutil
                    process = psutil.Process(os.getpid())
                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024
                    
                    if memory_mb > MAX_MEMORY_USAGE:
                        logger.warning(f"Memory usage ({memory_mb:.2f} MB) exceeds limit ({MAX_MEMORY_USAGE} MB). Using text-only mode.")
                        can_use_kokoro = False
                except ImportError:
                    logger.warning("psutil not available, assuming memory is available")
                
                if can_use_kokoro:
                    # Try to generate speech
                    tts_result, error = text_to_speech(ai_text, voice)
                    
                    response = {
                        "status": "success", 
                        "response": ai_text,
                        "text": ai_text
                    }
                    
                    # Add audio data if available
                    if tts_result:
                        response["audio"] = tts_result
                        response["format"] = "base64"
                        response["voice"] = voice
                    else:
                        # No audio, return text only with a message
                        response["low_memory_mode"] = True
                        response["message"] = error
                    
                    return generate_response(
                        200, 
                        response,
                        {"X-Response-Text": ai_text[:100]}
                    )
                else:
                    # Memory limit reached, return text-only response
                    return generate_response(
                        200, 
                        {
                            "status": "success", 
                            "response": ai_text,
                            "text": ai_text,
                            "low_memory_mode": True,
                            "message": "Running in low-memory mode. Voice synthesis will happen in the browser."
                        },
                        {"X-Response-Text": ai_text[:100]}
                    )
            except Exception as e:
                return generate_response(500, {"error": str(e), "details": traceback.format_exc()})
        
        if path == "/api/login":
            username = body.get("username", "") if isinstance(body, dict) else ""
            
            return generate_response(200, {
                "status": "success", 
                "message": f"Welcome, {username}!",
                "user": {"username": username, "role": "user"}
            })
        
        return generate_response(404, {"error": "Endpoint not found", "path": path})
    
    # Handle other HTTP methods
    return generate_response(405, {"error": "Method not allowed"})

def generate_response(status_code, body, headers=None):
    """Generate a standardized response for serverless functions"""
    response = {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Expose-Headers": "X-Response-Text",
            "Access-Control-Allow-Credentials": "true"
        },
        "body": json.dumps(body)
    }
    
    # Add any additional headers
    if headers and isinstance(headers, dict):
        for key, value in headers.items():
            response["headers"][key] = value
    
    return response 