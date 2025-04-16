from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import parse_qs
import os

def generate_response(status_code, content, content_type="application/json"):
    """Generate an HTTP response with the given status code and content."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": content_type,
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        },
        "body": content,
    }

def get_path_parts(path):
    """Extract path parts from a URL path."""
    # Remove leading slash and split by slash
    parts = path.lstrip('/').split('/')
    return parts

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle OPTIONS requests (CORS preflight)."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')

    def do_GET(self):
        """Handle GET requests."""
        # Respond with a simple test message
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response = {"status": "success", "message": "API is running"}
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_POST(self):
        """Handle POST requests."""
        path = self.path
        path_parts = get_path_parts(path)
        
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        request_body = self.rfile.read(content_length).decode('utf-8')
        
        # Set default response
        response_data = {"status": "error", "message": "Invalid endpoint"}
        status_code = 404
        
        try:
            # Parse JSON body if content exists
            request_json = {}
            if request_body:
                request_json = json.loads(request_body)
            
            # Handle different endpoints
            if path.startswith('/api/text') or path.startswith('/server/text'):
                # Handle text generation endpoint (simplified for testing)
                user_input = request_json.get('text', '')
                if not user_input:
                    response_data = {"status": "error", "message": "No input text provided"}
                    status_code = 400
                else:
                    # Just return a test response for now
                    response_data = {
                        "status": "success", 
                        "response": f"Echo: {user_input}"
                    }
                    status_code = 200
            
            elif path.startswith('/api/voice') or path.startswith('/server/voice'):
                # Handle voice generation endpoint (simplified for testing)
                response_data = {"status": "success", "message": "Voice endpoint reached"}
                status_code = 200
            
            elif path.startswith('/api/login') or path.startswith('/server/login'):
                # Handle login endpoint
                username = request_json.get('username', '')
                password = request_json.get('password', '')
                
                if not username or not password:
                    response_data = {"status": "error", "message": "Username and password are required"}
                    status_code = 400
                else:
                    # For testing purposes only - in a real app, use proper auth
                    if username == "test" and password == "password":
                        response_data = {
                            "status": "success",
                            "message": "Login successful",
                            "token": "test-token-12345"
                        }
                    else:
                        response_data = {"status": "error", "message": "Invalid credentials"}
                    
                    status_code = 200
            
            else:
                # Unknown endpoint
                response_data = {"status": "error", "message": f"Unknown endpoint: {path}"}
                status_code = 404
        
        except json.JSONDecodeError:
            # Handle JSON parsing errors
            response_data = {"status": "error", "message": "Invalid JSON in request body"}
            status_code = 400
        
        except Exception as e:
            # Handle general errors
            response_data = {"status": "error", "message": f"Server error: {str(e)}"}
            status_code = 500
        
        # Send response
        self.send_response(status_code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

# For direct testing outside of Vercel
def test(event, context):
    path = event.get('path', '')
    method = event.get('httpMethod', 'GET')
    headers = event.get('headers', {})
    body = event.get('body', '{}')
    
    if method == 'OPTIONS':
        return generate_response({"status": "ok"})
    
    if method == 'GET':
        return generate_response({
            "status": "ok",
            "message": "Interview AI API is running",
            "path": path,
            "method": method
        })
    
    if method == 'POST':
        try:
            request_data = json.loads(body)
            user_text = request_data.get('text', '')
        except:
            user_text = "Error parsing JSON"
        
        if "/api/text" in path:
            return generate_response({
                "response": f"API response for: {user_text}",
                "endpoint": "text"
            })
        elif "/api/voice" in path:
            return generate_response({
                "response": f"Voice response for: {user_text}",
                "endpoint": "voice"
            })
        else:
            return generate_response({
                "response": f"Unknown endpoint: {path}",
                "endpoint": "unknown"
            })
    
    return generate_response({"error": "Method not allowed"}, 405) 