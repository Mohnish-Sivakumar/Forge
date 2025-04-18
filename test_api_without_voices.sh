#!/bin/bash

# Set API base URL - change if needed
API_URL="http://localhost:5001"

# Terminal colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}---------------------------------------${NC}"
echo -e "${BLUE}Testing Interview AI API (Text-Only Mode)${NC}"
echo -e "${BLUE}---------------------------------------${NC}"

# Test 1: Check debug endpoint
echo -e "\n${YELLOW}Testing debug endpoint...${NC}"
curl -s $API_URL/api/debug | jq . 2>/dev/null || echo "Response is not valid JSON"

# Test 2: Test text endpoint with a sample request
echo -e "\n${YELLOW}Testing text API with sample request...${NC}"
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"text":"What makes a good software engineer?"}' \
  $API_URL/api/text | jq . 2>/dev/null || echo "Response is not valid JSON"

# Test 3: Test voice API with text-only fallback
echo -e "\n${YELLOW}Testing voice API (should fallback to text-only)...${NC}"
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"text":"Tell me briefly about your interview experience", "voice":"default"}' \
  $API_URL/api/voice | jq . 2>/dev/null || echo "Response is not valid JSON"

echo -e "\n${BLUE}---------------------------------------${NC}"
echo -e "${GREEN}Test Complete${NC}"
echo -e "${BLUE}---------------------------------------${NC}"
echo -e "\n${YELLOW}Note:${NC} This test is designed to work even without voice files installed."
echo -e "The voice API should return text responses without errors."
echo -e "Run with: ${GREEN}bash test_api_without_voices.sh${NC}\n" 