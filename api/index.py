from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import google.generativeai as genai
import speech_recognition as sr
from kokoro import KPipeline
import numpy as np
import io
import logging
import soundfile as sf
import os

app = Flask(__name__)

# Allow CORS for all origins
CORS(app)

logging.basicConfig(level=logging.DEBUG)

# Initialize services
genai.configure(api_key=os.environ.get("GOOGLE_GENAI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')
pipeline = KPipeline(lang_code='a')  # Only supports basic initialization

def process_text_chunk(text):
    try:
        generator = pipeline(text, voice='af_heart')
        for _, _, audio in generator:
            buffer = io.BytesIO()
            sf.write(buffer, audio, 24000, format='WAV')
            buffer.seek(0)
            audio_data = buffer.read()
            logging.debug(f"Audio data size: {len(audio_data)} bytes")
            yield audio_data  # Use yield instead of return to handle all chunks
    except Exception as e:
        logging.error(f"Error processing chunk: {e}")

def generate_speech_chunks(text):
    chunks = [c.strip() + '.' for c in text.split('.') if c.strip()]
    for chunk in chunks:
        if chunk:
            for audio in process_text_chunk(chunk):  # Iterate over all audio chunks
                if audio:
                    logging.debug("Yielding audio chunk")
                    yield audio

@app.route('/')
def home():
    return "Welcome to the Voice Assistant API!"

@app.route('/voice', methods=['POST'])
def voice_assistant():
    try:
        logging.info("Voice assistant endpoint called")
        data = request.json
        if not data:
            logging.error("No JSON data received")
            return jsonify({'error': 'No JSON data received'}), 400
            
        user_input = data.get('text', '')
        logging.info(f"Received user input: {user_input}")
        
        if not user_input:
            logging.error("No input text provided")
            return jsonify({'error': 'No input text provided'}), 400
            
        prompt = f"""
        Respond to: {user_input}
        Important: Provide your response as a continuous paragraph without line breaks or bullet points.
        Keep punctuation minimal, using mostly commas and periods. Your response must be concise and strictly limited to a maximum of 30 words. Remember you're an 
        interviewer. Ask the questions, and provide feedback after hearing the response from the user.
        Understand the context of the interview, and then ask a single question each time. After you hear the user's response, provide feedback on their response. Don't ask follow-up questions but tell them what specifically in their response was good and bad, why it was bad, and what could have been improved, and then move on to the next question.
        """
        
        response_text = model.generate_content(prompt).text
        response_text = ' '.join(response_text.split())
        
        logging.info(f"Generated response: {response_text}")

        return Response(
            stream_with_context(generate_speech_chunks(response_text)),
            mimetype='audio/wav'
        )

    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500 