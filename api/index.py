import json
import os
import sys
import traceback
import logging
from http.server import BaseHTTPRequestHandler
import google.generativeai as genai

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

def lazy_load_kokoro(force=False):
    """Lazily loads the Kokoro TTS library only when needed"""
    global kokoro_instance
    
    # If we already have a loaded instance and not forcing a reload, return it
    if kokoro_instance is not None and not force:
        return kokoro_instance
    
    # If we're in memory saving mode, only load if we have room
    if MEMORY_SAVING_MODE:
        # Check current memory usage
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            logger.info(f"Current memory usage: {memory_mb:.2f} MB")
            
            if memory_mb > MAX_MEMORY_USAGE:
                logger.warning(f"Memory usage ({memory_mb:.2f} MB) exceeds limit ({MAX_MEMORY_USAGE} MB). Using text-only mode.")
                return None
        except ImportError:
            logger.warning("psutil not available, cannot check memory usage")
    
    try:
        # Only import here to avoid loading these heavy libraries if not needed
        import kokoro
        
        # Create minimal configuration to reduce memory usage
        pipeline = kokoro.load_tts_pipeline(
            "hexgrad/Kokoro-82M",
            low_vram=True,  # Enable low VRAM mode
            cache_dir="/tmp/kokoro_cache"  # Use tmp directory for caching
        )
        
        logger.info("Kokoro TTS pipeline loaded successfully in low-memory mode")
        kokoro_instance = pipeline
        return kokoro_instance
    except Exception as e:
        logger.error(f"Failed to load Kokoro: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def cleanup_kokoro():
    """Clean up Kokoro resources to free memory"""
    global kokoro_instance
    
    if kokoro_instance is not None:
        try:
            # Release resources
            del kokoro_instance
            
            # Force garbage collection
            import gc
            gc.collect()
            
            logger.info("Kokoro resources cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up Kokoro: {str(e)}")
        finally:
            kokoro_instance = None

def text_to_speech(text, voice_option='default'):
    """
    Convert text to speech, with memory usage awareness.
    Will fall back to text-only mode if memory is constrained.
    """
    # Try to lazily load Kokoro
    pipeline = lazy_load_kokoro()
    
    # If we couldn't load Kokoro, return text-only response
    if pipeline is None:
        logger.info(f"Using text-only mode for: {text[:50]}...")
        return {
            "text": text,
            "audio": None,
            "format": "text-only",
            "low_memory_mode": True
        }
    
    try:
        logger.info(f"Generating speech for text: {text[:50]}...")
        
        # Determine voice ID based on option
        voice_id = "af_heart"  # default female voice
        if voice_option == "male1":
            voice_id = "am_michael"
        elif voice_option == "male2":
            voice_id = "am_adam"
        
        # Generate speech
        audio_array = pipeline(text, voice_id=voice_id)
        
        # Convert to base64 for transport
        import base64
        import numpy as np
        audio_bytes = audio_array.astype(np.float32).tobytes()
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        # Clean up to free memory
        cleanup_kokoro()
        
        return {
            "text": text,
            "audio": audio_b64,
            "format": "base64",
            "voice": voice_id
        }
    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Clean up in case of error
        cleanup_kokoro()
        
        # Return text-only response
        return {
            "text": text,
            "audio": None,
            "format": "text-only",
            "error": str(e)
        }

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
                tts_result = text_to_speech(ai_text, voice)
                
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
                if tts_result.get("audio"):
                    response["audio"] = tts_result.get("audio")
                    response["format"] = tts_result.get("format", "base64")
                    response["voice"] = tts_result.get("voice", voice)
                else:
                    # No audio, return text only with a message
                    response["low_memory_mode"] = True
                    response["message"] = "Running in low-memory mode. Voice synthesis will happen in the browser."
                
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
                    tts_result = text_to_speech(ai_text, voice)
                    
                    response = {
                        "status": "success", 
                        "response": ai_text,
                        "text": ai_text
                    }
                    
                    # Add audio data if available
                    if tts_result.get("audio"):
                        response["audio"] = tts_result.get("audio")
                        response["format"] = tts_result.get("format", "base64")
                        response["voice"] = tts_result.get("voice", voice)
                    else:
                        # No audio, return text only with a message
                        response["low_memory_mode"] = True
                        response["message"] = "Running in low-memory mode. Voice synthesis will happen in the browser."
                    
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