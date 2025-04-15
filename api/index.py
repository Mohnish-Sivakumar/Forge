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
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "message": "Interview AI API is running",
            "endpoints": ["/api/text", "/api/voice"],
            "usage": "Send POST requests to these endpoints with JSON body: {'text': 'Your question'}"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode())
            user_input = data.get('text', '')
            
            if not user_input:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = {"error": "No input text provided"}
                self.wfile.write(json.dumps(error_response).encode())
                return
                
            # Generate response with Gemini AI
            model = get_model()
            prompt = f"""
            Respond to: {user_input}
            Important: Provide your response as a continuous paragraph without line breaks or bullet points.
            Keep punctuation minimal, using mostly commas and periods. Your response must be concise and strictly limited to a maximum of 30 words. Remember you're an 
            interviewer. Ask the questions, and provide feedback after hearing the response from the user.
            """
            
            response_text = model.generate_content(prompt).text
            response_text = ' '.join(response_text.split())
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"response": response_text}
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"error": str(e)}
            self.wfile.write(json.dumps(error_response).encode()) 