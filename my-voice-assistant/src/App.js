import React, { useState, useRef, useEffect } from 'react';
import './App.css';

// Function to get the API base URL
const getApiBaseUrl = () => {
  const hostname = window.location.hostname;
  const port = window.location.port;
  const protocol = window.location.protocol;
  
  let baseUrl = '';
  
  // Local development
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    // Using the proxy configured in package.json (port 5001)
    baseUrl = '';
  } 
  // Production
  else {
    baseUrl = `${protocol}//${hostname}${port ? ':' + port : ''}`;
  }
  
  console.log('API Base URL:', baseUrl + '/api');
  return baseUrl + '/api';
};

// Constants for voice options
const API_BASE_URL = getApiBaseUrl();
console.log('Using API URL:', API_BASE_URL);

// Voice options
const VOICE_OPTIONS = [
  { id: 'default', name: 'Standard English' },
  { id: 'female1', name: 'Female Voice 1' },
  { id: 'female2', name: 'Emotional Female' },
  { id: 'male1', name: 'Narrative Male' },
  { id: 'male2', name: 'Conversational Male' },
  { id: 'british', name: 'British English' },
  { id: 'australian', name: 'Australian English' }
];

function App() {
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [isWaiting, setIsWaiting] = useState(false);
  const [aiResponse, setAiResponse] = useState(''); // Store AI's text response
  const [error, setError] = useState(''); // Error state
  const [selectedVoice, setSelectedVoice] = useState('default'); // Default voice
  const [useVoiceApi, setUseVoiceApi] = useState(true); // Whether to use voice API
  const [loading, setLoading] = useState(false); // Loading state
  const [response, setResponse] = useState(''); // Response from API (may be redundant with aiResponse)
  
  const recognitionRef = useRef(null);
  const speechResultRef = useRef(''); // Store the speech result
  const audioRef = useRef(new Audio());
  const audioContextRef = useRef(null);
  const audioSourceRef = useRef(null);

  // Helper function to speak text using browser's built-in speech synthesis
  const speakWithBrowserTTS = (text) => {
    if (!text) {
      console.warn('No text provided for browser TTS');
      return;
    }
    
    if (!window.speechSynthesis) {
      console.warn('Browser does not support speech synthesis');
      return;
    }
    
    // Stop any existing speech or audio
    stopAudioPlayback();
    
    console.log('Using browser TTS fallback');
    setSpeaking(true);
    
    // Split long text into smaller chunks to improve reliability
    // Browser speech synthesis can struggle with very long texts
    const MAX_CHUNK_LENGTH = 200;
    const textChunks = [];
    
    // Function to split text into sentences/chunks
    const splitTextIntoChunks = (text) => {
      if (text.length <= MAX_CHUNK_LENGTH) {
        return [text];
      }
      
      const sentences = text.match(/[^.!?]+[.!?]+/g) || [];
      const chunks = [];
      let currentChunk = '';
      
      sentences.forEach(sentence => {
        // If adding this sentence would make the chunk too long, start a new chunk
        if (currentChunk.length + sentence.length > MAX_CHUNK_LENGTH && currentChunk.length > 0) {
          chunks.push(currentChunk.trim());
          currentChunk = '';
        }
        
        // If a single sentence is too long, split it further
        if (sentence.length > MAX_CHUNK_LENGTH) {
          // If we have accumulated text, add it first
          if (currentChunk.length > 0) {
            chunks.push(currentChunk.trim());
            currentChunk = '';
          }
          
          // Split long sentence by commas if possible
          const segments = sentence.split(/, /);
          if (segments.length > 1) {
            let segment = '';
            segments.forEach(part => {
              if (segment.length + part.length + 2 > MAX_CHUNK_LENGTH) {
                chunks.push(segment.trim());
                segment = part + ', ';
              } else {
                segment += part + ', ';
              }
            });
            if (segment.length > 0) {
              chunks.push(segment.trim());
            }
          } else {
            // No commas, just split by length
            let i = 0;
            while (i < sentence.length) {
              const chunk = sentence.substr(i, MAX_CHUNK_LENGTH);
              chunks.push(chunk.trim());
              i += MAX_CHUNK_LENGTH;
            }
          }
        } else {
          currentChunk += sentence;
        }
      });
      
      // Add any remaining text
      if (currentChunk.length > 0) {
        chunks.push(currentChunk.trim());
      }
      
      return chunks;
    };
    
    const chunks = splitTextIntoChunks(text);
    console.log(`Split text into ${chunks.length} chunks for browser TTS`);
    
    // Select a voice
    let selectedVoice = null;
    try {
      const voices = window.speechSynthesis.getVoices();
      if (voices.length > 0) {
        // Try to use a good quality voice - prefer female voices in English
        const englishVoices = voices.filter(voice => voice.lang.includes('en-'));
        if (englishVoices.length > 0) {
          // Prefer female voices if available
          const femaleVoice = englishVoices.find(voice => 
            voice.name.toLowerCase().includes('female') || 
            voice.name.toLowerCase().includes('samantha') ||
            voice.name.toLowerCase().includes('victoria'));
          
          selectedVoice = femaleVoice || englishVoices[0];
        }
      }
    } catch (e) {
      console.warn('Error selecting voice for TTS:', e);
    }
    
    // Check if voices are loaded yet
    if (selectedVoice === null && window.speechSynthesis.getVoices().length === 0) {
      // Voices not loaded yet, try again when they're ready
      window.speechSynthesis.onvoiceschanged = () => {
        // Try call again once voices are loaded
        window.speechSynthesis.onvoiceschanged = null; // Prevent infinite loop
        speakWithBrowserTTS(text);
      };
      return;
    }
    
    // Track speaking state
    let chunkIndex = 0;
    const speakNextChunk = () => {
      if (chunkIndex >= chunks.length) {
        // All done
        console.log('Browser TTS finished speaking all chunks');
        setSpeaking(false);
        return;
      }
      
      const chunk = chunks[chunkIndex];
      const utterance = new SpeechSynthesisUtterance(chunk);
      
      // Set the selected voice if available
      if (selectedVoice) {
        utterance.voice = selectedVoice;
      }
      
      // Use a slightly slower rate and moderate pitch for better clarity
      utterance.rate = 0.95;
      utterance.pitch = 1.0;
      
      utterance.onend = () => {
        console.log(`Browser TTS finished chunk ${chunkIndex + 1}/${chunks.length}`);
        chunkIndex++;
        // Continue with next chunk
        speakNextChunk();
      };
      
      utterance.onerror = (event) => {
        console.error(`Browser TTS error on chunk ${chunkIndex + 1}:`, event);
        // Try to continue with next chunk on error
        chunkIndex++;
        speakNextChunk();
      };
      
      try {
        console.log(`Speaking chunk ${chunkIndex + 1}/${chunks.length}`);
        window.speechSynthesis.speak(utterance);
      } catch (e) {
        console.error('Error speaking with browser TTS:', e);
        // Try to continue with next chunk
        chunkIndex++;
        setTimeout(speakNextChunk, 100);
      }
    };
    
    // Start speaking
    speakNextChunk();
  };

  // Stop any ongoing audio playback
  const stopAudioPlayback = () => {
    // Stop any playing audio elements
    if (window.activeAudio) {
      try {
        window.activeAudio.pause();
        if (window.activeAudioURL) {
          URL.revokeObjectURL(window.activeAudioURL);
          window.activeAudioURL = null;
        }
        window.activeAudio = null;
      } catch (e) {
        console.error('Error stopping audio:', e);
      }
    }
    
    // Cancel any browser speech synthesis
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    
    setSpeaking(false);
  };

  // Initialize audio context
  useEffect(() => {
    // Initialize audio context (only when needed to avoid warning)
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    
    // Clean up on unmount
    return () => {
      stopAudioPlayback();
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(console.error);
      }
    };
  }, []);

  // Initialize audio system
  useEffect(() => {
    // Initialize global audio references
    window.activeAudio = null;
    window.activeAudioURL = null;
    
    // Pre-load voices for browser TTS
    if (window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
      };
    }
    
    // Cleanup when component unmounts
    return () => {
      stopAudioPlayback();
    };
  }, []);

  const toggleListening = () => {
    // Clear any previous errors
    setError('');
    
    if (listening) {
      console.log('Stopping speech recognition');
      recognitionRef.current?.stop();
      setListening(false);
    } else {
      console.log('Initializing speech recognition');
      // Check if speech recognition is supported
      if (!window.webkitSpeechRecognition && !window.SpeechRecognition) {
        setError('Speech recognition not supported in this browser');
        return;
      }
      
      const SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition;
      const recognition = new SpeechRecognition();
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
          if (useVoiceApi) {
            fetchVoiceResponse(speechResultRef.current, selectedVoice);
          } else {
            fetchTextResponse(speechResultRef.current);
          }
          speechResultRef.current = ''; // Clear the stored result
        }
      };

      recognitionRef.current = recognition;

      // Start recognition immediately
      recognition.start();
      setListening(true);
    }
  };

  // Fetch text-only response
  const fetchTextResponse = async (text) => {
    setIsWaiting(true);
    setSpeaking(true);
    setError(''); // Clear any previous errors
    setLoading(true);
    
    // Stop any ongoing audio playback
    stopAudioPlayback();
    
    // Use the calculated API URL
    const apiUrl = `${API_BASE_URL}/text`;
    
    try {
      console.log('Sending request to API with text:', text);
      console.log('Using API URL:', apiUrl);
      
      // Then send the actual POST request
      const textResponse = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text })
      });
      
      console.log('Text response status:', textResponse.status);
      
      if (textResponse.ok) {
        const jsonData = await textResponse.json();
        console.log('Text response data:', jsonData);
        
        if (jsonData.response) {
          setAiResponse(jsonData.response);
          setResponse(jsonData.response); // Also update response state
          
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
          setResponse(`Error: ${jsonData.error}`); // Also update response state
          setError(`API Error: ${jsonData.error}`);
          setSpeaking(false);
        } else {
          console.error('No response field in JSON data');
          setAiResponse('Error: Could not retrieve response from API');
          setResponse('Error: Could not retrieve response from API'); // Also update response state
          setError('The API returned an unexpected response format');
          setSpeaking(false);
        }
      } else {
        console.error(`Failed to get text response: ${textResponse.status}`);
        // Try to get error message from response if possible
        try {
          const errorData = await textResponse.json();
          console.log('Error response:', errorData);
          setError(`API Error (${textResponse.status}): ${errorData.message || 'Unknown error'}`);
        } catch {
          setError(`API Error: The server returned status ${textResponse.status}`);
        }
        const errorMessage = `Error: Failed to get response from API (Status ${textResponse.status})`;
        setAiResponse(prevResponse => prevResponse || errorMessage);
        setResponse(prevResponse => prevResponse || errorMessage); // Also update response state
        setSpeaking(false);
      }
      
      // Mark as no longer waiting
      setIsWaiting(false);
      setLoading(false);
    } catch (error) {
      console.error('Network error in fetch operation:', error);
      setSpeaking(false);
      setError(`Network error: ${error.message}`);
      const errorMessage = 'Error: ' + error.message;
      setAiResponse(prevResponse => prevResponse || errorMessage);
      setResponse(prevResponse => prevResponse || errorMessage); // Also update response state
      setIsWaiting(false);
      setLoading(false);
    }
  };

  // Fetch voice response with Kokoro
  const fetchVoiceResponse = async (inputText, selectedVoice) => {
    // Reset audio if we have one already playing
    if (window.activeAudio) {
      try {
        window.activeAudio.pause();
        if (window.activeAudioURL) {
          URL.revokeObjectURL(window.activeAudioURL);
          window.activeAudioURL = null;
        }
        window.activeAudio = null;
      } catch (e) {
        console.error('Error stopping audio:', e);
      }
    }
    
    setLoading(true);
    setError('');
    setSpeaking(false);
    
    try {
      console.log(`Fetching voice response for: "${inputText.substring(0, 30)}..." with voice: ${selectedVoice}`);
      
      // Make request to API - Don't add /api/ again as it's already in API_BASE_URL
      const response = await fetch(`${API_BASE_URL}/voice`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: inputText,
          voice: selectedVoice
        }),
        // Increase timeout for larger audio files
        timeout: 30000
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // Check content type to decide how to process the response
      const contentType = response.headers.get('Content-Type') || '';
      console.log('Response Content-Type:', contentType);
      
      // Handle binary audio response (WAV file)
      if (contentType.includes('audio/') || contentType === 'application/octet-stream') {
        console.log('Received binary audio data');
        
        // Get the audio data as a blob
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        // Create and set up audio element
        const audio = new Audio(audioUrl);
        window.activeAudio = audio;
        window.activeAudioURL = audioUrl;
        
        // Set up event listeners
        audio.oncanplaythrough = () => {
          console.log('Audio can play through');
          setSpeaking(true);
          audio.play().catch(err => {
            console.error('Audio playback error:', err);
            setError('Audio playback failed. Using browser TTS instead.');
            speakWithBrowserTTS(inputText);
          });
        };
        
        audio.onended = () => {
          console.log('Audio playback finished');
          setSpeaking(false);
          setAiResponse(inputText);
        };
        
        audio.onerror = (e) => {
          console.error('Audio error:', e);
          setError('Audio playback error. Using browser TTS instead.');
          setSpeaking(false);
          speakWithBrowserTTS(inputText);
        };
        
        // Set timeout for audio loading
        const audioTimeout = setTimeout(() => {
          if (!audio.canPlayType(contentType) && !audio.canPlayType('audio/wav')) {
            console.error('Browser cannot play this audio format');
            setError('Browser cannot play the received audio format. Using browser TTS instead.');
            speakWithBrowserTTS(inputText);
          }
        }, 10000); // 10 second timeout
        
        // Clear timeout when audio loads
        audio.onloadeddata = () => {
          clearTimeout(audioTimeout);
        };
      } 
      // Handle JSON response
      else {
        // Parse the JSON response
        const data = await response.json();
        console.log('Response data:', data);
        
        if (data.error) {
          throw new Error(data.error);
        }
        
        if (data.audio) {
          console.log('Received audio data in JSON response');
          
          // Process the audio data
          let audioData;
          if (data.compressed && window.pako) {
            // Decompress using pako if available
            console.log('Decompressing audio data...');
            try {
              const compressedData = Uint8Array.from(atob(data.audio), c => c.charCodeAt(0));
              audioData = window.pako.inflate(compressedData);
            } catch (e) {
              console.error('Error decompressing audio:', e);
              throw new Error('Failed to decompress audio data');
            }
          } else {
            // Convert base64 to binary
            audioData = Uint8Array.from(atob(data.audio), c => c.charCodeAt(0));
          }
          
          // Create audio blob and URL
          const audioBlob = new Blob([audioData], { type: 'audio/wav' });
          const audioUrl = URL.createObjectURL(audioBlob);
          
          // Create and play the audio
          const audio = new Audio(audioUrl);
          window.activeAudio = audio;
          window.activeAudioURL = audioUrl;
          
          // Set up event listeners
          audio.oncanplaythrough = () => {
            console.log('Audio can play through');
            setSpeaking(true);
            audio.play().catch(err => {
              console.error('Audio playback error:', err);
              setError('Audio playback failed. Using browser TTS instead.');
              speakWithBrowserTTS(inputText);
            });
          };
          
          audio.onended = () => {
            console.log('Audio playback finished');
            setSpeaking(false);
            setAiResponse(inputText);
          };
          
          audio.onerror = (e) => {
            console.error('Audio error:', e);
            setError('Audio playback error. Using browser TTS instead.');
            setSpeaking(false);
            speakWithBrowserTTS(inputText);
          };
          
          // Set timeout for audio loading
          const audioTimeout = setTimeout(() => {
            console.error('Audio loading timeout');
            setError('Audio loading timeout. Using browser TTS instead.');
            speakWithBrowserTTS(inputText);
          }, 10000); // 10 second timeout
          
          // Clear timeout when audio loads
          audio.onloadeddata = () => {
            clearTimeout(audioTimeout);
          };
        } else {
          // No audio data in response, use browser TTS fallback
          console.log('No audio data received. Using browser TTS.');
          speakWithBrowserTTS(inputText);
        }
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching voice response:', error);
      setError(`Error: ${error.message}`);
      setLoading(false);
      // Fallback to browser TTS
      speakWithBrowserTTS(inputText);
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
        
        {/* Voice options */}
        <div className="voice-options">
          <label>
            <input
              type="checkbox"
              checked={useVoiceApi}
              onChange={() => setUseVoiceApi(!useVoiceApi)}
            />
            Use enhanced voice
          </label>
          
          {useVoiceApi && (
            <div className="voice-selector">
              <select 
                value={selectedVoice} 
                onChange={(e) => setSelectedVoice(e.target.value)}
                disabled={speaking || isWaiting}
              >
                {VOICE_OPTIONS.map(voice => (
                  <option key={voice.id} value={voice.id}>{voice.name}</option>
                ))}
              </select>
            </div>
          )}
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