#!/bin/bash

echo "Testing debug endpoint..."
curl -s http://localhost:5001/api/debug | jq .

echo -e "\nTesting voice endpoint..."
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"text":"Help me with my interview", "voice":"default", "format":"json"}' \
  http://localhost:5001/api/voice | jq .

echo -e "\nTest complete!" 