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
echo -e "${BLUE}Testing Interview AI API Endpoints${NC}"
echo -e "${BLUE}---------------------------------------${NC}"

# Test 1: Check API home endpoint
echo -e "\n${YELLOW}Testing API home endpoint...${NC}"
curl -s -o /dev/null -w "Status: %{http_code}\n" $API_URL/

# Test 2: Check debug endpoint
echo -e "\n${YELLOW}Testing debug endpoint...${NC}"
curl -s -X GET $API_URL/api/debug | jq . 2>/dev/null || echo "Response is not valid JSON"

# Test 3: Test OPTIONS request to text endpoint (CORS preflight)
echo -e "\n${YELLOW}Testing OPTIONS preflight request to /api/text...${NC}"
curl -s -X OPTIONS -o /dev/null -w "Status: %{http_code}\n" \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  $API_URL/api/text

# Test 4: Test text API with a sample request
echo -e "\n${YELLOW}Testing text API with sample request...${NC}"
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"text":"What makes a good software engineer?"}' \
  $API_URL/api/text | jq . 2>/dev/null || echo "Response is not valid JSON"

# Test 5: Check voice API headers (without downloading full audio)
echo -e "\n${YELLOW}Testing voice API headers...${NC}"
curl -s -I -X POST \
  -H "Content-Type: application/json" \
  -d '{"text":"Tell me about yourself"}' \
  $API_URL/api/voice

echo -e "\n${BLUE}---------------------------------------${NC}"
echo -e "${BLUE}API Testing Complete${NC}"
echo -e "${BLUE}---------------------------------------${NC}"
echo -e "\n${GREEN}Note:${NC} Make sure you have the API running on $API_URL"
echo -e "Run the server with: ${YELLOW}cd backend && flask run --port=5001${NC}\n" 