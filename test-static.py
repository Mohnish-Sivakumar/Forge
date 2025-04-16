#!/usr/bin/env python3
"""
Simple script to test static file serving
"""
import os
import sys
from flask import Flask, send_from_directory
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Get path to static files
current_dir = os.path.dirname(os.path.abspath(__file__))
static_folder = os.path.join(current_dir, "my-voice-assistant/build")
app.static_folder = static_folder
app.static_url_path = ''

logger.info(f"Static folder set to: {static_folder}")

# Check if static folder exists
if not os.path.exists(static_folder):
    logger.error(f"Static folder does not exist: {static_folder}")
    sys.exit(1)

# List files in static folder
logger.info("Files in static folder:")
for root, dirs, files in os.walk(static_folder):
    for file in files:
        logger.info(f"  {os.path.join(root, file)}")

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if path.startswith('static/'):
        logger.info(f"Serving static file: {path}")
        return send_from_directory(app.static_folder, path)
    else:
        logger.info(f"Serving index.html for path: {path}")
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting test server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True) 