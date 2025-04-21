#!/bin/bash

# Set the Deepgram API key - replace with your actual key
export DEEPGRAM_API_KEY="your-deepgram-api-key"
export GEMINI_API_KEY="your-gemini-api-key"

# Echo the configuration
echo "Testing Deepgram TTS integration"
echo "================================="
echo "DEEPGRAM_API_KEY: ${DEEPGRAM_API_KEY:0:5}...${DEEPGRAM_API_KEY:(-5)}"
echo "GEMINI_API_KEY: ${GEMINI_API_KEY:0:5}...${GEMINI_API_KEY:(-5)}"
echo "================================="

# Make a test request to the TTS endpoint
echo "Making test request to TTS endpoint..."
curl -v -X POST \
  -H "Content-Type: application/json" \
  -d '{"text":"This is a test of the Deepgram text-to-speech API integration.", "voice":"aura-2-thalia-en", "encoding":"linear16", "container":"wav"}' \
  http://localhost:5001/api/tts -o test-output.wav

# Check if the output file was created
if [ -f test-output.wav ]; then
  echo "Successfully created test-output.wav ($(du -h test-output.wav | cut -f1) bytes)"
else
  echo "Failed to create output file"
fi

echo "Test complete!" 