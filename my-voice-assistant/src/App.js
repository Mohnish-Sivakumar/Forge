import React, { useState, useRef } from 'react';
import './App.css';

function App() {
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [isWaiting, setIsWaiting] = useState(false);
  const [aiResponse, setAiResponse] = useState(''); // Store AI's text response
  const recognitionRef = useRef(null);
  const speechResultRef = useRef(''); // Store the speech result
  const audioSourceRef = useRef(null);

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

  // Stop any ongoing audio playback
  const stopAudioPlayback = () => {
    if (audioSourceRef.current) {
      try {
        audioSourceRef.current.stop();
        audioSourceRef.current.disconnect();
        audioSourceRef.current = null;
      } catch (error) {
        console.warn('Error stopping audio:', error);
      }
    }
  };

  const fetchResponse = async (text) => {
    setIsWaiting(true);
    setSpeaking(true);
    
    // Stop any ongoing audio playback
    stopAudioPlayback();
    
    try {
      console.log('Sending request to API with text:', text);
      
      // Try to fetch debug info first (helpful for troubleshooting)
      try {
        const debugResponse = await fetch('/api/debug', {
          method: 'GET'
        });
        
        if (debugResponse.ok) {
          const debugInfo = await debugResponse.json();
          console.log('API Debug info:', debugInfo);
        }
      } catch (debugError) {
        console.warn('Could not fetch debug info:', debugError);
      }
      
      // First get text response for immediate feedback
      const textResponse = await fetch('/api/text', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text })
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
        console.error(`Failed to get text response: ${textResponse.status}`);
        setAiResponse(`Error: Failed to get response from API (Status ${textResponse.status})`);
        setSpeaking(false);
        setIsWaiting(false);
        return;
      }
      
      // Then get voice response to play audio
      console.log('Fetching voice response...');
      const audioResponse = await fetch('/api/voice', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text })
      });
      
      console.log('Voice response status:', audioResponse.status);
      
      if (audioResponse.ok) {
        // Get the text response from headers if available
        const headerText = audioResponse.headers.get('X-Response-Text');
        if (headerText && headerText !== aiResponse) {
          setAiResponse(headerText);
          console.log('Updated response from headers:', headerText);
        }
      
        // Process the audio stream
        try {
          const reader = audioResponse.body.getReader();
          const audioContext = new (window.AudioContext || window.webkitAudioContext)();
          
          let audioChunks = [];
          let totalLength = 0;
          
          console.log('Reading audio stream...');
          while (true) {
            const {done, value} = await reader.read();
            if (done) break;
            
            if (value) {
              audioChunks.push(value);
              totalLength += value.length;
            }
          }
          
          console.log(`Received ${totalLength} bytes of audio data`);
          
          if (totalLength > 0) {
            // Combine all chunks into a single array
            const combinedChunks = new Uint8Array(totalLength);
            let offset = 0;
            
            for (const chunk of audioChunks) {
              combinedChunks.set(chunk, offset);
              offset += chunk.length;
            }
            
            console.log('Decoding audio data...');
            
            // Decode and play the audio
            audioContext.decodeAudioData(combinedChunks.buffer, (buffer) => {
              console.log('Audio decoded successfully, starting playback');
              const source = audioContext.createBufferSource();
              source.buffer = buffer;
              source.connect(audioContext.destination);
              
              // Save reference to stop if needed
              audioSourceRef.current = source;
              
              // Handle playback completion
              source.onended = () => {
                console.log('Audio playback completed');
                setSpeaking(false);
                audioSourceRef.current = null;
              };
              
              // Start playback
              source.start(0);
              console.log('Audio playback started');
            }, (error) => {
              console.error('Error decoding audio:', error);
              setSpeaking(false);
              
              // Fallback to browser's speech synthesis
              if ('speechSynthesis' in window) {
                console.log('Falling back to browser speech synthesis');
                const utterance = new SpeechSynthesisUtterance(aiResponse);
                utterance.onend = () => setSpeaking(false);
                window.speechSynthesis.speak(utterance);
              }
            });
          } else {
            console.error('No audio data received');
            setSpeaking(false);
            
            // Fallback to browser's speech synthesis
            if ('speechSynthesis' in window) {
              console.log('Falling back to browser speech synthesis');
              const utterance = new SpeechSynthesisUtterance(aiResponse);
              utterance.onend = () => setSpeaking(false);
              window.speechSynthesis.speak(utterance);
            }
          }
        } catch (audioError) {
          console.error('Error processing audio:', audioError);
          setSpeaking(false);
          
          // Fallback to browser's speech synthesis
          if ('speechSynthesis' in window) {
            console.log('Falling back to browser speech synthesis due to error');
            const utterance = new SpeechSynthesisUtterance(aiResponse);
            utterance.onend = () => setSpeaking(false);
            window.speechSynthesis.speak(utterance);
          }
        }
      } else {
        console.error(`Failed to get audio response: ${audioResponse.status}`);
        setSpeaking(false);
        
        // Fallback to browser's speech synthesis
        if ('speechSynthesis' in window) {
          console.log('Falling back to browser speech synthesis due to failed request');
          const utterance = new SpeechSynthesisUtterance(aiResponse);
          utterance.onend = () => setSpeaking(false);
          window.speechSynthesis.speak(utterance);
        }
      }
      
    } catch (error) {
      console.error('Error in fetch operation:', error);
      setSpeaking(false);
      setAiResponse(prevResponse => prevResponse || 'Error: ' + error.message);
      
      // Fallback to browser's speech synthesis in case of error
      if ('speechSynthesis' in window && aiResponse) {
        const utterance = new SpeechSynthesisUtterance(aiResponse);
        utterance.onend = () => setSpeaking(false);
        window.speechSynthesis.speak(utterance);
      }
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
