from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        # Handle OPTIONS requests (CORS preflight)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization')
        self.end_headers()
        return
        
    def do_GET(self):
        # Simple response for GET requests
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # For debugging purposes
        response = {
            "status": "ok",
            "message": "Interview AI API is running",
            "path": self.path,
            "environ": dict(os.environ),
            "headers": dict(self.headers)
        }
        
        self.wfile.write(json.dumps(response).encode())
        return

    def do_POST(self):
        # Parse the path to handle different endpoints
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # Get POST data
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            post_data = self.rfile.read(content_length)
            try:
                request_data = json.loads(post_data)
                user_text = request_data.get('text', '')
            except Exception as e:
                user_text = f"Error parsing JSON: {str(e)}"
        else:
            user_text = "No data provided"
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Debug information
        debug_info = {
            "received_path": self.path,
            "parsed_path": path,
            "method": self.command,
            "headers": dict(self.headers),
            "content_length": content_length,
            "user_text": user_text
        }
        
        # Check which endpoint was accessed - handling various path formats
        if path == '/api/text' or path.startswith('/api/text/'):
            response = {
                "response": f"This is a test response from the API for input: {user_text}. Actual AI integration will be added after deployment works.",
                "debug": debug_info
            }
        elif path == '/api/voice' or path.startswith('/api/voice/'):
            response = {
                "response": f"This is a voice response from the API for input: {user_text}. Voice functionality will be added later.",
                "debug": debug_info
            }
        else:
            response = {
                "response": f"Unknown endpoint: {path}",
                "debug": debug_info
            }
        
        self.wfile.write(json.dumps(response).encode()) 