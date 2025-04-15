from http.server import BaseHTTPRequestHandler
import json
import google.generativeai as genai

# Initialize Gemini AI
GEMINI_API_KEY = "AIzaSyDrxMRoQ-Knm7gM_6YNHAiPhXoC6HN09S4"
genai.configure(api_key=GEMINI_API_KEY)

# Create the model only once (lazy loading)
_model = None

def get_model():
    global _model
    if _model is None:
        _model = genai.GenerativeModel('gemini-1.5-flash')
    return _model

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        # Handle OPTIONS requests (CORS preflight)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version')
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
            "message": "Interview AI API is running"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return

    def do_POST(self):
        # Handle POST requests
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # Set response headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            # Parse the request body
            data = json.loads(post_data.decode())
            user_input = data.get('text', '')
            
            if not user_input:
                response = {"error": "No input text provided"}
                self.wfile.write(json.dumps(response).encode())
                return
                
            # Generate response with Gemini AI
            model = get_model()
            prompt = f"""
            Respond to: {user_input}
            Important: Keep your response concise, under 30 words.
            """
            
            response_text = model.generate_content(prompt).text
            response_text = ' '.join(response_text.split())
            
            # Return the AI response
            response = {"response": response_text}
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            # Handle errors
            response = {"error": str(e)}
            self.wfile.write(json.dumps(response).encode()) 