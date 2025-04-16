import React, { useState, useRef } from 'react';
import './App.css';

function App() {
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [isWaiting, setIsWaiting] = useState(false);
  const [aiResponse, setAiResponse] = useState(''); // Store AI's text response
  const [error, setError] = useState(''); // New error state
  const recognitionRef = useRef(null);
  const speechResultRef = useRef(''); // Store the speech result
  const audioSourceRef = useRef(null);

  const toggleListening = () => {
    // Clear any previous errors
    setError('');
    
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
        setError(`Speech recognition error: ${event.error}`);
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
    setError(''); // Clear any previous errors
    
    // Stop any ongoing audio playback
    stopAudioPlayback();
    
    // Get current domain to handle different deployments
    const apiBase = window.location.origin;
    const apiUrl = `${apiBase}/api/text`;
    
    try {
      console.log('Sending request to API with text:', text);
      console.log('Using API URL:', apiUrl);
      
      // First send an OPTIONS request for CORS preflight
      console.log('Sending OPTIONS preflight...');
      try {
        await fetch(apiUrl, {
          method: 'OPTIONS',
          headers: {
            'Origin': window.location.origin,
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
          }
        });
        console.log('OPTIONS preflight completed');
      } catch (preflightError) {
        console.log('OPTIONS preflight failed, continuing anyway:', preflightError);
        // Continue anyway as browser may handle this automatically
      }
      
      // Then send the actual POST request
      const textResponse = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Origin': window.location.origin
        },
        body: JSON.stringify({ text })
      });
      
      console.log('Text response status:', textResponse.status);
      
      if (textResponse.ok) {
        const jsonData = await textResponse.json();
        console.log('Text response data:', jsonData);
        
        if (jsonData.response) {
          setAiResponse(jsonData.response);
          
          // Use browser's speech synthesis
          if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(jsonData.response);
            utterance.onend = () => setSpeaking(false);
            window.speechSynthesis.speak(utterance);
          } else {
            setSpeaking(false);
          }
        } else if (jsonData.error) {
          console.error('Error from API:', jsonData.error);
          setAiResponse(`Error: ${jsonData.error}`);
          setError(`API Error: ${jsonData.error}`);
          setSpeaking(false);
        } else {
          console.error('No response field in JSON data');
          setAiResponse('Error: Could not retrieve response from API');
          setError('The API returned an unexpected response format');
          setSpeaking(false);
        }
      } else {
        console.error(`Failed to get text response: ${textResponse.status}`);
        // Try to get error message from response if possible
        try {
          const errorData = await textResponse.json();
          console.log('Error response:', errorData);
          setError(`API Error (${textResponse.status}): ${errorData.response || 'Unknown error'}`);
        } catch {
          setError(`API Error: The server returned status ${textResponse.status}`);
        }
        setAiResponse(`Error: Failed to get response from API (Status ${textResponse.status})`);
        setSpeaking(false);
      }
      
      // Mark as no longer waiting
      setIsWaiting(false);
    } catch (error) {
      console.error('Network error in fetch operation:', error);
      setSpeaking(false);
      setError(`Network error: ${error.message}`);
      setAiResponse(prevResponse => prevResponse || 'Error: ' + error.message);
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
        
        {/* Display error message if present */}
        {error && (
          <div className="error-message">
            <p>{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
