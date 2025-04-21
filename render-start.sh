#!/bin/bash
# Render start script with Voice RSS API and Deepgram integration

# Set environment variables
export SERVE_STATIC=true
export VOICE_RSS_API_KEY="25b4ce640dcf4aaf8ce3af6bd9b2c3b9"
export DEEPGRAM_API_KEY="your-deepgram-api-key"

# Print information
echo "=== Render Deployment Settings ==="
echo "Using Voice RSS API: true"
echo "Using Deepgram TTS API: true"
echo "Voice RSS API Key: ${VOICE_RSS_API_KEY:0:5}...${VOICE_RSS_API_KEY:(-5)}" # Show only prefix and suffix for security
echo "Deepgram API Key: ${DEEPGRAM_API_KEY:0:5}...${DEEPGRAM_API_KEY:(-5)}" # Show only prefix and suffix for security
echo "================================="

# Install dependencies
echo "==> Installing required packages..."
pip install flask==2.2.3 werkzeug==2.2.3 flask-cors==3.0.10 google-generativeai==0.3.1 requests>=2.28.0 psutil>=5.9.0

# Print debug information
echo "==> Python version: $(python --version)"
echo "==> Installed packages:"
pip list | grep -E 'flask|werkzeug|requests|psutil|google-generativeai'

# Create voice files directory (for backward compatibility)
mkdir -p api/voice_files

# Start the server
echo "==> Starting application with TTS APIs enabled..."
gunicorn api.index:handler --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 