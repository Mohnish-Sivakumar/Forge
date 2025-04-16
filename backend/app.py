from flask import Flask, request, jsonify, Response, stream_with_context, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
import logging
import os
import json
import kokoro
import io

# Check if we're serving static files too (combined deployment)
SERVE_STATIC = os.environ.get("SERVE_STATIC", "False").lower() in ("true", "1", "t")

# Set path to static files - make sure it's absolute
if SERVE_STATIC:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    static_folder = os.path.join(os.path.dirname(current_dir), "my-voice-assistant/build")
    print(f"==> Setting static folder to: {static_folder}")
else:
    static_folder = None

app = Flask(__name__, static_folder=static_folder, static_url_path='')
CORS(app, resources={r"/*": {"origins": "*"}})
logging.basicConfig(level=logging.INFO)

# Initialize Gemini API with API key from environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDrxMRoQ-Knm7gM_6YNHAiPhXoC6HN09S4")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize kokoro for voice synthesis
pipeline = kokoro.KPipeline(lang_code='a')  # Basic initialization

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({"status": "healthy"})

@app.route('/')
def home():
    if SERVE_STATIC:
        print("==> Serving index.html from static folder")
        return send_from_directory(app.static_folder, 'index.html')
    return jsonify({"message": "Welcome to the Interview AI API!"})

@app.route('/<path:path>')
def serve_static_files(path):
    if SERVE_STATIC:
        # Don't serve API routes as static files
        if path.startswith('api/'):
            return jsonify({"error": "Not found"}), 404
            
        # Check if file exists and serve it
        file_path = os.path.join(app.static_folder, path)
        if os.path.isfile(file_path):
            print(f"==> Serving static file: {path}")
            return send_from_directory(app.static_folder, path)
            
        # For all other paths return index.html (for React routing)
        print(f"==> Path not found, serving index.html for: {path}")
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

@app.route('/api/voice', methods=['POST', 'OPTIONS'])
def voice_response():
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
        
        # Generate text response first
        prompt = f"""
        Respond to: {user_input}
        Important: Provide your response as a continuous paragraph without line breaks or bullet points.
        Keep punctuation minimal, using mostly commas and periods. Your response must be concise and strictly limited to a maximum of 30 words.
        """
        
        response_text = model.generate_content(prompt).text
        response_text = ' '.join(response_text.split())
        
        logging.info(f"Generated voice response: {response_text}")
        
        # For now, instead of generating real audio, return a success response with the text
        # This helps test that the endpoint works before implementing full voice functionality
        return jsonify({
            "status": "success", 
            "response": response_text,
            "message": "Voice endpoint reached - text response provided while audio is in development"
        })
        
    except Exception as e:
        logging.error(f"Error in voice response: {e}")
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