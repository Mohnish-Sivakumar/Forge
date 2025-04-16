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
        self.send_header('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization, Content-Type')
        self.end_headers()
        return
        
    def do_GET(self):
        # Simple response for GET requests
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        origin = self.headers.get('Origin', 'No origin header')
        host = self.headers.get('Host', 'No host header')
        
        # For debugging purposes
        response = {
            "status": "ok",
            "message": "Interview AI API is running",
            "path": self.path,
            "method": self.command,
            "client_origin": origin,
            "server_host": host,
            "custom_flag": os.environ.get('USE_CUSTOM_URLS', 'Not set')
        }
        
        self.wfile.write(json.dumps(response).encode())
        return

    def do_POST(self):
        # Always respond with 200 OK for POST requests
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # Parse the path to handle different endpoints
        raw_path = self.path
        parsed_path = urllib.parse.urlparse(raw_path)
        path = parsed_path.path
        
        # Get POST data
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = b'{}'
        user_text = "No data provided"
        
        if content_length > 0:
            try:
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data)
                user_text = request_data.get('text', '')
            except Exception as e:
                user_text = f"Error parsing JSON: {str(e)}"
        
        # Get origin information from headers
        origin = self.headers.get('Origin', 'No origin header')
        host = self.headers.get('Host', 'No host header')
        
        # Debug information
        debug_info = {
            "raw_path": raw_path,
            "parsed_path": path,
            "method": self.command,
            "content_length": content_length,
            "user_text": user_text,
            "client_origin": origin,
            "server_host": host
        }
        
        # Handle different endpoints with better path matching
        if path == '/api/text' or path == '/api/text/' or path.startswith('/api/text?'):
            response = {
                "response": f"API response for: {user_text}",
                "debug": debug_info
            }
        elif path == '/api/voice' or path == '/api/voice/' or path.startswith('/api/voice?'):
            response = {
                "response": f"Voice response for: {user_text}",
                "debug": debug_info
            }
        else:
            response = {
                "response": f"Unknown endpoint: {path}",
                "debug": debug_info
            }
        
        self.wfile.write(json.dumps(response).encode()) 