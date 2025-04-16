from http.server import BaseHTTPRequestHandler
import json
import os

def generate_response(body, status_code=200):
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With"
        }
    }

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())
        
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "status": "ok",
            "message": "Interview AI API is running",
            "path": self.path,
            "method": "GET",
            "endpoint": "text" if "/text" in self.path else "voice" if "/voice" in self.path else "unknown"
        }
        
        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Get POST data
        content_length = int(self.headers.get('Content-Length', 0))
        user_text = "No data provided"
        
        if content_length > 0:
            try:
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data)
                user_text = request_data.get('text', '')
            except Exception as e:
                user_text = f"Error parsing JSON: {str(e)}"
        
        # Handle different endpoints
        if "/api/text" in self.path:
            response = {
                "response": f"API response for: {user_text}",
                "endpoint": "text"
            }
        elif "/api/voice" in self.path:
            response = {
                "response": f"Voice response for: {user_text}",
                "endpoint": "voice"
            }
        else:
            response = {
                "response": f"Unknown endpoint: {self.path}",
                "endpoint": "unknown"
            }
        
        self.wfile.write(json.dumps(response).encode())

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