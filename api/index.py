from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'message': 'API is running',
            'status': 'ok'
        }
        
        self.wfile.write(json.dumps(response).encode())
        
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            if post_data:
                data = json.loads(post_data.decode('utf-8'))
                user_text = data.get('text', '')
                
                if user_text:
                    # Simple response without dependencies
                    response = {
                        'response': f"You said: {user_text}. This is a test response from the simplified API."
                    }
                else:
                    response = {
                        'error': 'No text input provided'
                    }
            else:
                response = {
                    'error': 'No data provided'
                }
                
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            error_response = {
                'error': f'Error processing request: {str(e)}'
            }
            self.wfile.write(json.dumps(error_response).encode()) 