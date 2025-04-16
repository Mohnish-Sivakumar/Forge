from flask import Flask, request, jsonify, Response, stream_with_context, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
import logging
import os
import json
import kokoro

# Check if we're serving static files too (combined deployment)
SERVE_STATIC = os.environ.get("SERVE_STATIC", "False").lower() in ("true", "1", "t")
static_folder = "../my-voice-assistant/build" if SERVE_STATIC else None

app = Flask(__name__, static_folder=static_folder)
CORS(app, resources={r"/*": {"origins": "*"}})
logging.basicConfig(level=logging.INFO)

# Initialize Gemini API with API key from environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDrxMRoQ-Knm7gM_6YNHAiPhXoC6HN09S4")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({"status": "healthy"})

@app.route('/')
def home():
    if SERVE_STATIC:
        return send_from_directory(app.static_folder, 'index.html')
    return jsonify({"message": "Welcome to the Interview AI API!"})

# Serve static files if SERVE_STATIC is enabled
@app.route('/<path:path>')
def serve_static(path):
    if SERVE_STATIC:
        if path.startswith('api/'):
            # Don't try to serve API calls as static files
            return jsonify({"error": "Not found"}), 404
        elif os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            # Return index.html for client-side routing
            return send_from_directory(app.static_folder, 'index.html')
    return jsonify({"error": "Not found"}), 404

@app.route('/api/text', methods=['POST', 'OPTIONS'])
def text_response():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        user_input = data.get('text', '')
        
        if not user_input:
            return jsonify({"status": "error", "message": "No input text provided"}), 400
            
        prompt = f"""
        Respond to: {user_input}
        Important: Provide your response as a continuous paragraph without line breaks or bullet points.
        Keep punctuation minimal, using mostly commas and periods. Your response must be concise and strictly limited to a maximum of 30 words. Remember you're an 
        interviewer. Ask the questions, and provide feedback after hearing the response from the user.
        """
        
        response_text = model.generate_content(prompt).text
        response_text = ' '.join(response_text.split())
        
        logging.info(f"Generated response: {response_text}")
        
        return jsonify({"status": "success", "response": response_text})
    
    except Exception as e:
        logging.error(f"Error in text response: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        username = data.get('username', '')
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({"status": "error", "message": "Username and password are required"}), 400
            
        # For testing purposes only - in a real app, use proper auth
        if username == "test" and password == "password":
            return jsonify({
                "status": "success",
                "message": "Login successful",
                "token": "test-token-12345"
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Invalid credentials"
            }), 401
    
    except Exception as e:
        logging.error(f"Error in login: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def _build_cors_preflight_response():
    response = jsonify({})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port) 