import React, { useState, useRef } from 'react';
import './App.css';

function App() {
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [isWaiting, setIsWaiting] = useState(false);
  const [aiResponse, setAiResponse] = useState(''); // Store AI's text response
  const recognitionRef = useRef(null);
  const speechResultRef = useRef(''); // Store the speech result

  const toggleListening = () => {
    if (listening) {
      console.log('Stopping speech recognition');
      recognitionRef.current.stop();
      setListening(false);
    } else {
      console.log('Initializing speech recognition');
      const recognition = new window.webkitSpeechRecognition();
      recognition.lang = 'en-US';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      recognition.continuous = true; // Allow continuous listening

      recognition.onstart = () => {
        console.log('Speech recognition started');
        setAiResponse(''); // Clear previous response
      };

      recognition.onresult = (event) => {
        const speechResult = event.results[0][0].transcript;
        console.log('Speech received: ' + speechResult);
        speechResultRef.current = speechResult; // Store the result
      };

      recognition.onspeechend = () => {
        console.log('Speech ended');
        // Do not stop recognition here to allow continuous listening
      };

      recognition.onerror = (event) => {
        console.error('Recognition error:', event.error);
        setListening(false);
      };

      recognition.onend = () => {
        console.log('Speech recognition ended');
        // Ensure UI updates are triggered
        if (speechResultRef.current) {
          fetchResponse(speechResultRef.current);
          speechResultRef.current = ''; // Clear the stored result
        }
      };

      recognitionRef.current = recognition;

      // Start recognition immediately
      recognition.start();
      setListening(true);
    }
  };

  const fetchResponse = async (text) => {
    setIsWaiting(true);
    setSpeaking(true);
    
    try {
      console.log('Sending request to API with text:', text);
      
      // Try to fetch debug info first
      try {
        const debugResponse = await fetch('/api/debug', {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
          mode: 'cors',
        });
        
        if (debugResponse.ok) {
          const debugInfo = await debugResponse.json();
          console.log('API Debug info:', debugInfo);
        }
      } catch (debugError) {
        console.warn('Could not fetch debug info:', debugError);
      }
      
      // First get text response
      const textResponse = await fetch('/api/text', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ text }),
        mode: 'cors',
      });
      
      console.log('Text response status:', textResponse.status);
      
      if (textResponse.ok) {
        const jsonData = await textResponse.json();
        console.log('Text response data:', jsonData);
        
        if (jsonData.response) {
          setAiResponse(jsonData.response);
        } else {
          console.error('No response field in JSON data');
          setAiResponse('Error: Could not retrieve response from API');
        }
      } else {
        console.error(`Failed to get text response: ${textResponse.status} ${textResponse.statusText}`);
        if (textResponse.status === 401) {
          setAiResponse('Error: Authentication required for the API. Please check server configuration.');
        } else if (textResponse.status === 405) {
          setAiResponse('Error: API endpoint not accepting POST requests. Please check server configuration.');
        } else {
          setAiResponse(`Error: Failed to get response from API (Status ${textResponse.status})`);
        }
        // Don't attempt audio if text failed with auth error
        setSpeaking(false);
        setIsWaiting(false);
        return;
      }
      
      // Then get audio response
      const audioResponse = await fetch('/api/voice', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'audio/wav',
        },
        body: JSON.stringify({ text }),
        mode: 'cors',
      });
      
      if (audioResponse.ok) {
        try {
          const reader = audioResponse.body.getReader();
          const audioContext = new (window.AudioContext || window.webkitAudioContext)();
          
          let audioChunks = [];
          let totalLength = 0;
          
          while (true) {
            const {done, value} = await reader.read();
            if (done) break;
            
            if (value) {
              audioChunks.push(value);
              totalLength += value.length;
            }
          }
          
          if (totalLength > 0) {
            console.log(`Processing ${totalLength} bytes of audio data`);
            const combinedChunks = new Uint8Array(totalLength);
            let offset = 0;
            
            for (const chunk of audioChunks) {
              combinedChunks.set(chunk, offset);
              offset += chunk.length;
            }
            
            const audioBuffer = await audioContext.decodeAudioData(combinedChunks.buffer);
            const source = audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(audioContext.destination);
            source.onended = () => {
              setSpeaking(false);
            };
            source.start(0);
            console.log('Audio playback started');
          } else {
            console.error('No audio data received');
            setSpeaking(false);
          }
        } catch (audioError) {
          console.error('Error processing audio:', audioError);
          setSpeaking(false);
        }
      } else {
        console.error(`Failed to get audio response: ${audioResponse.status} ${audioResponse.statusText}`);
        if (audioResponse.status === 401) {
          console.error('Authentication required for the API endpoint');
          // Use speech synthesis as fallback
          if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(aiResponse);
            window.speechSynthesis.speak(utterance);
            utterance.onend = () => {
              setSpeaking(false);
            };
          } else {
            setSpeaking(false);
          }
        } else {
          setSpeaking(false);
        }
      }
      
    } catch (error) {
      console.error('Error in fetch operation:', error);
      setSpeaking(false);
      setAiResponse(aiResponse => aiResponse || 'Error: ' + error.message);
    } finally {
      setIsWaiting(false);
    }
  };

  return (
    <div className="App">
      <div className="background-square"></div>
      <div className="header">
        <h1>Interview AI</h1>
        <p>Enhance your interview skills with real-time feedback and practice.</p>
      </div>
      <div className="container">
        <div className={`blob ${speaking ? 'speaking' : ''}`}>
          <div className="blob-inner">
            {/* Display AI response text */}
            {aiResponse && (
              <div className="ai-response-text">
                <p>{aiResponse}</p>
              </div>
            )}
          </div>
        </div>
        
        <button 
          className={`mic-button ${listening ? 'listening' : ''}`}
          onClick={toggleListening} 
          disabled={speaking || isWaiting}
        >
          <div className="mic-icon"></div>
        </button>

        {isWaiting && <div className="waiting-indicator"></div>}
        
        <div className="status-text">
          {listening ? 'Listening...' : speaking ? 'Speaking...' : 'Click to speak'}
        </div>
      </div>
    </div>
  );
}

export default App;
