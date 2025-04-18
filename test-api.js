#!/usr/bin/env node
import fetch from 'node-fetch';

// Function to test the API
async function testAPI() {
  try {
    // First test the debug endpoint
    console.log("Testing debug endpoint...");
    const debugResponse = await fetch('http://localhost:5001/api/debug');
    const debugData = await debugResponse.json();
    console.log("Debug endpoint response:", debugData);
    
    // Test the voice endpoint
    console.log("\nTesting voice endpoint...");
    const voiceResponse = await fetch('http://localhost:5001/api/voice', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: "Help me with my interview",
        voice: "default",
        format: "json"
      })
    });
    
    console.log("Voice endpoint status:", voiceResponse.status);
    console.log("Voice endpoint headers:", Object.fromEntries(voiceResponse.headers));
    
    const voiceData = await voiceResponse.json();
    console.log("Voice endpoint response:", {
      status: voiceData.status,
      response: voiceData.response,
      hasAudio: !!voiceData.audio
    });
    
    console.log("\nAPI Test Successful!");
  } catch (error) {
    console.error("Error testing API:", error);
  }
}

// Run the test
testAPI(); 