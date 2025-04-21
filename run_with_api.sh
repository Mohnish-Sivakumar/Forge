#!/bin/bash

# Set environment variables for API keys
export SPEECHIFY_API_KEY="fwsjj7SjBEmJ9C058GN5NLEEIfwOga3tYKkftbo_TQE="
export GEMINI_API_KEY="AIzaSyDrxMRoQ-Knm7gM_6YNHAiPhXoC6HN09S4"

# Print API key information
echo "=== Starting Voice Assistant with API Keys ==="
echo "Speechify API Key: ${SPEECHIFY_API_KEY:0:5}...${SPEECHIFY_API_KEY:(-5)}"
echo "Gemini API Key: ${GEMINI_API_KEY:0:5}...${GEMINI_API_KEY:(-5)}"

# Run the dev.cjs script which starts both the frontend and backend
node dev.cjs 