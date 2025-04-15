from http.server import BaseHTTPRequestHandler
import json

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
        
        response = {
            "status": "ok",
            "message": "Interview AI API is running",
            "path": self.path
        }
        
        self.wfile.write(json.dumps(response).encode())
        return

    def do_POST(self):
        # Handle POST requests for different paths
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            post_data = self.rfile.read(content_length)
            try:
                request_data = json.loads(post_data)
                user_text = request_data.get('text', '')
            except:
                user_text = "No valid JSON data provided"
        else:
            user_text = "No data provided"
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Check which endpoint was accessed
        if self.path == '/api/text' or self.path.startswith('/api/text?'):
            response = {
                "response": f"This is a test response from the API for input: {user_text}. Actual AI integration will be added after deployment works."
            }
        elif self.path == '/api/voice' or self.path.startswith('/api/voice?'):
            response = {
                "response": f"This is a voice response from the API for input: {user_text}. Voice functionality will be added later."
            }
        else:
            response = {
                "response": f"Unknown endpoint: {self.path}"
            }
        
        self.wfile.write(json.dumps(response).encode()) 