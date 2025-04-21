import json
import os
import sys
import traceback
import logging
from http.server import BaseHTTPRequestHandler
import google.generativeai as genai
import gc
import base64
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure API key
api_key = os.environ.get("GEMINI_API_KEY", "your-api-key")
genai.configure(api_key=api_key)

# Speechify API configuration
SPEECHIFY_API_KEY = os.environ.get("SPEECHIFY_API_KEY", "fwsjj7SjBEmJ9C058GN5NLEEIfwOga3tYKkftbo_TQE=")
SPEECHIFY_API_URL = "https://api.sws.speechify.com/v1/audio/speech"

# Check if Speechify API key is set
if SPEECHIFY_API_KEY == "your-speechify-api-key":
    logger.warning("⚠️ SPEECHIFY_API_KEY not set! Using placeholder value which will cause API errors.")
else:
    logger.info(f"Speechify API key configured: {SPEECHIFY_API_KEY[:5]}...{SPEECHIFY_API_KEY[-5:] if len(SPEECHIFY_API_KEY) > 10 else ''}")

# Setup Gemini model
model = genai.GenerativeModel("gemini-pro")

# Add diagnostic function for memory usage
def get_memory_usage():
    """Get current memory usage in MB"""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / 1024 / 1024
        return memory_usage_mb
    except ImportError:
        logger.warning("psutil not installed, cannot check memory usage")
        return 0

# Log memory usage at startup
startup_memory = get_memory_usage()
logger.info(f"Starting memory usage: {startup_memory:.2f}MB")

# Function to convert text to speech using Speechify API
def speechify_text_to_speech(text, voice_id='belinda'):
    """Convert text to speech using Speechify API"""
    try:
        logger.info(f"Processing text via Speechify API, length: {len(text)}")
        logger.info(f"Selected voice: {voice_id}")
        
        # Prepare request headers
        headers = {
            'Authorization': f'Bearer {SPEECHIFY_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Prepare request body
        payload = {
            'input': text,
            'voice_id': voice_id
        }
        
        # Log the API request details (without the full text for brevity)
        logger.info(f"Calling Speechify API with URL: {SPEECHIFY_API_URL}")
        logger.info(f"Request headers: {headers}")
        truncated_payload = {**payload, 'input': payload['input'][:50] + '...' if len(payload['input']) > 50 else payload['input']}
        logger.info(f"Request payload: {truncated_payload}")
        
        # Make the API request
        response = requests.post(SPEECHIFY_API_URL, headers=headers, json=payload)
        
        # Log the response status and headers
        logger.info(f"Speechify API response status: {response.status_code}")
        logger.info(f"Speechify API response headers: {response.headers}")
        
        # Check if the request was successful
        if response.status_code != 200:
            logger.error(f"Speechify API error: {response.status_code}")
            error_data = {}
            try:
                error_data = response.json()
                logger.error(f"Speechify API error response: {error_data}")
            except:
                logger.error(f"Speechify API error response (not JSON): {response.text[:200]}")
                error_data = {"message": response.text}
                
            return {
                "status": "error",
                "response": text,
                "message": f"Speechify API error: {error_data.get('message', response.status_code)}"
            }
        
        # Process the successful JSON response
        speech_data = response.json()
        
        # Check if we have the audio_url in the response
        if 'audio_url' in speech_data:
            # Download the audio from the URL
            audio_response = requests.get(speech_data['audio_url'])
            if audio_response.status_code == 200:
                audio_data = audio_response.content
                logger.info(f"Successfully downloaded audio from Speechify API, size: {len(audio_data)} bytes")
                
                # Return audio data and content type
                return {
                    "status": "success",
                    "response": text,
                    "audio_data": audio_data,
                    "content_type": "audio/mp3"  # Assuming Speechify returns MP3 format
                }
            else:
                logger.error(f"Failed to download audio from URL: {speech_data['audio_url']}")
                return {
                    "status": "error",
                    "response": text,
                    "message": "Failed to download audio from Speechify API"
                }
        else:
            # Handle case where audio_url is missing
            logger.error(f"No audio_url in Speechify API response: {speech_data}")
            return {
                "status": "error",
                "response": text,
                "message": "No audio URL in Speechify API response"
            }
        
    except Exception as e:
        logger.error(f"Error in speechify_text_to_speech: {str(e)}")
        traceback.print_exc()
        return {
            "status": "error",
            "response": text,
            "message": f"Error in speechify_text_to_speech: {str(e)}"
        }

def list_available_voices():
    """List available voice options for Speechify"""
    try:
        # Speechify voices
        speechify_options = {
            "belinda": {"language": "en-us", "name": "Belinda (English)"},
            "matthew": {"language": "en-us", "name": "Matthew (English)"},
            "aria": {"language": "en-us", "name": "Aria (English)"},
            "ryan": {"language": "en-us", "name": "Ryan (English)"},
            "joseph": {"language": "en-us", "name": "Joseph (English)"},
            "tom": {"language": "en-us", "name": "Tom (English)"},
            "jane": {"language": "en-us", "name": "Jane (English)"} 
        }
        
        # Format the response
        voices_status = {}
        
        # Add Speechify voices
        for voice_id, info in speechify_options.items():
            voices_status[voice_id] = {
                "available": True,
                "name": info["name"],
                "language": info["language"],
                "provider": "speechify"
            }
        
        return {
            "voices": voices_status,
            "sources": ["speechify"],
            "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    except Exception as e:
        logger.error(f"Error listing voices: {str(e)}")
        return {
            "error": str(e),
            "memory_usage_mb": round(get_memory_usage(), 2)
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
                    }
                except ImportError:
                    pass
                
                response = {
                    "status": "ok",
                    "api_version": "1.0.0",
                    "python_version": sys.version,
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
                        "limit_mb": 450,
                        "within_limit": (mem_info.rss / 1024 / 1024) < 450
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
            
            # Log the incoming request for debugging
            logger.info(f"Received POST request to path: {path}")
            logger.info(f"Headers: {self.headers}")
            
            # Parse JSON data if content exists
            if content_length > 0:
                try:
                    post_data = json.loads(post_data)
                    logger.info(f"Request data: {json.dumps(post_data, indent=2)[:200]}...")
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

            # Handle Speechify TTS endpoint - both with and without api/ prefix
            if path == "api/tts" or path == "tts":
                logger.info("Handling TTS request")
                self._handle_tts_request(post_data)
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
        voice = post_data.get('voice', 'belinda')  # Default to Speechify voice
        
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
            can_use_tts = True
            try:
                import psutil
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                
                if memory_mb > 450:
                    logger.warning(f"Memory usage ({memory_mb:.2f} MB) exceeds limit ({450} MB). Using text-only mode.")
                    can_use_tts = False
            except ImportError:
                logger.warning("psutil not available, assuming memory is available")
            
            if can_use_tts:
                # Try to generate speech with Speechify
                tts_result = speechify_text_to_speech(ai_text, voice)
                
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
                if tts_result.get("status") == "success" and "audio_data" in tts_result:
                    # Base64 encode the audio data for JSON response
                    audio_base64 = base64.b64encode(tts_result["audio_data"]).decode('utf-8')
                    response["audio"] = audio_base64
                    response["format"] = "mp3"
                    response["voice"] = voice
                else:
                    # No audio, return text only with a message
                    response["low_memory_mode"] = True
                    response["message"] = tts_result.get("message", "Error generating audio")
                
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

    def _handle_tts_request(self, post_data):
        # Extract data from POST request
        text = post_data.get('text', '')
        voice = post_data.get('voice', 'belinda')
        
        logger.info(f"TTS Request: voice={voice}")
        
        if not text:
            logger.warning("TTS request missing text")
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            response = {"error": "No text provided"}
            self.wfile.write(json.dumps(response).encode())
            return

        try:
            # Generate speech with Speechify
            tts_result = speechify_text_to_speech(text, voice)
            
            if tts_result.get("status") == "success" and "audio_data" in tts_result:
                logger.info(f"Successfully generated Speechify audio, size: {len(tts_result['audio_data'])} bytes")
                # Send audio data directly
                self.send_response(200)
                content_type = tts_result.get('content_type', 'audio/mp3')
                logger.info(f"Sending response with Content-Type: {content_type}")
                self.send_header('Content-type', content_type)
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(tts_result["audio_data"])
                return
            else:
                # Send error response
                logger.error(f"Failed to generate Speechify audio: {tts_result.get('message', 'Unknown error')}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                response = {
                    "error": tts_result.get("message", "Error generating speech"),
                    "text": text
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
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
                }
            except ImportError:
                pass
                
            return generate_response(200, {
                "status": "ok",
                "api_version": "1.0.0",
                "python_version": sys.version,
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
                    "limit_mb": 450,
                    "within_limit": (mem_info.rss / 1024 / 1024) < 450
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
            voice = body.get("voice", "belinda") if isinstance(body, dict) else "belinda"
            
            if not text:
                return generate_response(400, {"error": "No text provided"})
            
            try:
                ai_response = model.generate_content(
                    f"You are an interview coach called Interview AI. Keep your response concise. Question: {text}"
                )
                ai_text = ai_response.text
                
                logger.info(f"Generated voice response: {ai_text[:100]}...")
                
                # Check memory before attempting voice synthesis
                can_use_tts = True
                try:
                    import psutil
                    process = psutil.Process(os.getpid())
                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024
                    
                    if memory_mb > 450:
                        logger.warning(f"Memory usage ({memory_mb:.2f} MB) exceeds limit ({450} MB). Using text-only mode.")
                        can_use_tts = False
                except ImportError:
                    logger.warning("psutil not available, assuming memory is available")
                
                if can_use_tts:
                    # Try to generate speech with Speechify
                    tts_result = speechify_text_to_speech(ai_text, voice)
                    
                    response = {
                        "status": "success", 
                        "response": ai_text,
                        "text": ai_text
                    }
                    
                    # Add audio data if available
                    if tts_result.get("status") == "success" and "audio_data" in tts_result:
                        # Base64 encode the audio data for JSON response
                        audio_base64 = base64.b64encode(tts_result["audio_data"]).decode('utf-8')
                        response["audio"] = audio_base64
                        response["format"] = "mp3"
                        response["voice"] = voice
                    else:
                        # No audio, return text only with a message
                        response["low_memory_mode"] = True
                        response["message"] = tts_result.get("message", "Error generating audio")
                    
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

        if path == "/api/tts":
            text = body.get("text", "") if isinstance(body, dict) else ""
            voice = body.get("voice", "belinda") if isinstance(body, dict) else "belinda"
            
            if not text:
                return generate_response(400, {"error": "No text provided"})
            
            try:
                # Generate speech with Speechify
                tts_result = speechify_text_to_speech(text, voice)
                
                if tts_result.get("status") == "success" and "audio_data" in tts_result:
                    # Return binary audio with appropriate headers
                    return {
                        "statusCode": 200,
                        "headers": {
                            "Content-Type": tts_result.get("content_type", "audio/mp3"),
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                            "Access-Control-Allow-Headers": "Content-Type, Authorization",
                        },
                        "body": base64.b64encode(tts_result["audio_data"]).decode('utf-8'),
                        "isBase64Encoded": True
                    }
                else:
                    # Return error message
                    return generate_response(500, {
                        "error": tts_result.get("message", "Error generating speech"),
                        "text": text
                    })
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