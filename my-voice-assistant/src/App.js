import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './App.css';
import { createClient } from '@deepgram/sdk';

// Function to get the API base URL
const getApiBaseUrl = () => {
  const hostname = window.location.hostname;
  const port = window.location.port;
  const protocol = window.location.protocol;
  
  let baseUrl = '';
  
  // Local development
  if (hostname === 'localhost' && port === '3000') {
    console.log('Using local development API base URL: http://localhost:5001');
    return 'http://localhost:5001';
  } 
  // Production on Render
  else if (hostname.includes('render.com')) {
    // Don't append '/api' since we're using the same domain for frontend and API
    baseUrl = `${protocol}//${hostname}${port ? ':' + port : ''}`;
    console.log('Using Render production API base URL:', baseUrl);
    return baseUrl;
  }
  // Other production environments
  else {
    baseUrl = `${protocol}//${hostname}${port ? ':' + port : ''}`;
    console.log('Using production API base URL:', baseUrl);
    return baseUrl;
  }
};

// Speechify API key (provided by user)
const SPEECHIFY_API_KEY = "fwsjj7SjBEmJ9C058GN5NLEEIfwOga3tYKkftbo_TQE=";

// Deepgram configuration - use environment variable in production
const DEEPGRAM_API_KEY = process.env.REACT_APP_DEEPGRAM_API_KEY || 'your-deepgram-api-key';
// Initialize Deepgram client - this will be used on the server side, not in the browser
// For browser usage, we'll use a proxy

// Utility function to check if a specific audio format is supported by the browser
const isSupportedAudioFormat = (format) => {
  const audio = new Audio();
  return audio.canPlayType(`audio/${format}`) !== '';
};

// Utility function to decode base64 audio data
const decodeAudioData = (base64Data) => {
  try {
    // Decode base64 string to binary
    const binaryString = atob(base64Data);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    
    return bytes.buffer;
  } catch (error) {
    console.error('Error decoding audio data:', error);
    return null;
  }
};

// Constants for voice options
const API_BASE_URL = getApiBaseUrl();
console.log('Using API URL:', API_BASE_URL);

// Voice options for Speechify
const VOICE_OPTIONS = [
  { id: 'belinda', name: 'Belinda (Default)' },
  { id: 'nick', name: 'Nick (Male)' },
  { id: 'kim', name: 'Kim (Female)' },
  { id: 'rohit', name: 'Rohit (Male)' },
  { id: 'rosemary', name: 'Rosemary (Female)' }
];

function App() {
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [isWaiting, setIsWaiting] = useState(false);
  const [aiResponse, setAiResponse] = useState(''); // Store AI's text response
  const [error, setError] = useState(''); // Error state
  const [selectedVoice, setSelectedVoice] = useState('belinda'); // Default voice
  const [useVoiceApi, setUseVoiceApi] = useState(true); // Whether to use voice API
  const [loading, setLoading] = useState(false); // Loading state
  const [response, setResponse] = useState(''); // Response from API (may be redundant with aiResponse)
  const [processingAudio, setProcessingAudio] = useState(false); // New state for audio processing
  const [browserSupport, setBrowserSupport] = useState({ // New state to track browser support
    speechRecognition: false,
    speechSynthesis: false,
    audioPlayback: false
  });
  const [interviewComplete, setInterviewComplete] = useState(false); // New state to track interview completion
  const [conversationHistory, setConversationHistory] = useState([]); // Store conversation history
  
  const recognitionRef = useRef(null);
  const speechResultRef = useRef(''); // Store the speech result
  const audioRef = useRef(new Audio());
  const audioContextRef = useRef(null);
  const audioSourceRef = useRef(null);

  // Check browser capabilities on mount
  useEffect(() => {
    checkBrowserSupport();
  }, []);

  // Check browser capabilities for voice features
  const checkBrowserSupport = () => {
    const support = {
      speechRecognition: !!(window.webkitSpeechRecognition || window.SpeechRecognition),
      speechSynthesis: !!(window.speechSynthesis),
      audioPlayback: !!(window.Audio && (new Audio()).canPlayType)
    };
    
    console.log('Browser capabilities:', support);
    setBrowserSupport(support);
    
    // Show error if basic features aren't supported
    if (!support.audioPlayback) {
      setError('Your browser does not support audio playback. Please use a modern browser.');
    } else if (!support.speechRecognition) {
      setError('Speech recognition is not supported in this browser. Try using Chrome, Edge, or Safari.');
    } else if (!support.speechSynthesis) {
      console.warn('Browser speech synthesis not available for fallback TTS.');
    }

    return support;
  };

  // Speak with Speechify TTS via proxy endpoint
  const speakWithSpeechify = async (text, voiceId = 'belinda') => {
    console.log(`Speaking with Speechify, voice: ${voiceId}, text length: ${text.length}`);
    
    if (!text) {
      console.error('No text provided for speech');
      return;
    }
    
    try {
      // Try using direct Speechify API first
      const success = await speakWithSpeechifyDirect(text, voiceId);
      if (success) {
        return; // If direct call worked, don't use proxy
      }
      
      setSpeaking(true);
      setError('');
      
      // Create the API URL
      const apiUrl = `${API_BASE_URL}/api/tts`;
      
      // Prepare request data
      const requestData = {
        text: text,
        voice: voiceId
      };
      
      console.log(`Fetching speech from ${apiUrl}`, requestData);
      
      // Set a timeout for the fetch request (10 seconds)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);
      
      // Make the request to the API
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
        signal: controller.signal
      });
      
      // Clear the timeout
      clearTimeout(timeoutId);
      
      // Check if the request was successful
      if (!response.ok) {
        const errorText = await response.text();
        console.error('TTS API error:', response.status, errorText);
        throw new Error(`API error: ${response.status} ${errorText}`);
      }
      
      // Check the content type to determine how to handle the response
      const contentType = response.headers.get('Content-Type') || '';
      
      if (contentType.includes('audio/')) {
        // Handle audio response directly
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        // Prepare the audio for playback
        if (audioRef.current) {
          audioRef.current.src = audioUrl;
          audioRef.current.addEventListener('ended', () => {
            setSpeaking(false);
            URL.revokeObjectURL(audioUrl);
          });
          audioRef.current.addEventListener('error', (e) => {
            console.error('Audio playback error:', e);
            setSpeaking(false);
            URL.revokeObjectURL(audioUrl);
            throw new Error('Error playing audio');
          });
          
          // Create a timeout to handle cases where audio doesn't play
          audioTimeoutRef.current = setTimeout(() => {
            console.warn('Audio playback timeout - falling back to browser TTS');
            URL.revokeObjectURL(audioUrl);
            setSpeaking(false);
            speakWithBrowserTTS(text);
          }, 10000);
          
          // Play the audio
          const playPromise = audioRef.current.play();
          if (playPromise) {
            playPromise.then(() => {
              console.log('Audio playback started');
            }).catch(error => {
              console.error('Audio play promise rejected:', error);
              URL.revokeObjectURL(audioUrl);
              setSpeaking(false);
              speakWithBrowserTTS(text);
            });
          }
        } else {
          console.error('Audio element reference is not available');
          setSpeaking(false);
          speakWithBrowserTTS(text);
        }
      } else if (contentType.includes('application/json')) {
        // Handle JSON response (likely an error)
        const jsonData = await response.json();
        console.error('TTS API returned JSON instead of audio:', jsonData);
        throw new Error(jsonData.error || 'Invalid response from TTS API');
      } else {
        // Handle unexpected content type
        console.error('Unexpected content type from TTS API:', contentType);
        throw new Error(`Unexpected content type: ${contentType}`);
      }
    } catch (error) {
      console.error('Error in speakWithSpeechify:', error);
      setSpeaking(false);
      
      // Fallback to browser TTS
      speakWithBrowserTTS(text);
    }
  };

  // Direct call to Speechify API (no proxy)
  const speakWithSpeechifyDirect = async (text, voiceId = 'belinda') => {
    console.log(`Speaking directly with Speechify API, voice: ${voiceId}, text length: ${text.length}`);
    
    if (!text) {
      console.error('No text provided for speech');
      return false;
    }
    
    try {
      setSpeaking(true);
      setError('');
      
      // Call the Speechify API directly
      console.log(`Calling Speechify API directly with voice: ${voiceId}`);
      
      // First try the stream endpoint
      try {
        console.log("Making request to Speechify stream endpoint...");
        const streamResponse = await fetch("https://api.sws.speechify.com/v1/audio/stream", {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${SPEECHIFY_API_KEY}`,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            "input": text,
            "voice_id": voiceId
          }),
        });
        
        console.log("Stream endpoint response status:", streamResponse.status);
        
        if (streamResponse.ok) {
          const audioBlob = await streamResponse.blob();
          const audioUrl = URL.createObjectURL(audioBlob);
          
          // Prepare the audio for playback
          if (audioRef.current) {
            audioRef.current.src = audioUrl;
            audioRef.current.addEventListener('ended', () => {
              setSpeaking(false);
              URL.revokeObjectURL(audioUrl);
            });
            audioRef.current.addEventListener('error', (e) => {
              console.error('Audio playback error:', e);
              setSpeaking(false);
              URL.revokeObjectURL(audioUrl);
              throw new Error('Error playing audio');
            });
            
            // Play the audio
            const playPromise = audioRef.current.play();
            if (playPromise) {
              playPromise.then(() => {
                console.log('Speechify audio playback started');
              }).catch(error => {
                console.error('Speechify audio play promise rejected:', error);
                URL.revokeObjectURL(audioUrl);
                setSpeaking(false);
                return false;
              });
            }
            return true;
          }
        } else {
          console.log("Stream endpoint failed with status:", streamResponse.status);
          const errorText = await streamResponse.text();
          console.error("Stream endpoint error:", errorText);
        }
      } catch (streamError) {
        console.error("Error calling stream endpoint:", streamError);
      }
      
      // If stream endpoint fails, try the speech endpoint
      try {
        console.log("Stream endpoint failed, trying speech endpoint...");
        console.log("Making request to Speechify speech endpoint...");
        const speechResponse = await fetch("https://api.sws.speechify.com/v1/audio/speech", {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${SPEECHIFY_API_KEY}`,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            "input": text,
            "voice_id": voiceId
          }),
        });
        
        console.log("Speech endpoint response status:", speechResponse.status);
        
        if (speechResponse.ok) {
          const jsonData = await speechResponse.json();
          console.log("Speech endpoint response:", jsonData);
          
          if (jsonData.audio_url) {
            // Play the audio from the URL
            audioRef.current.src = jsonData.audio_url;
            audioRef.current.addEventListener('ended', () => {
              setSpeaking(false);
            });
            audioRef.current.addEventListener('error', (e) => {
              console.error('Audio playback error:', e);
              setSpeaking(false);
              throw new Error('Error playing audio from URL');
            });
            
            // Play the audio
            const playPromise = audioRef.current.play();
            if (playPromise) {
              playPromise.then(() => {
                console.log('Speechify audio playback started from URL');
              }).catch(error => {
                console.error('Speechify audio play promise rejected:', error);
                setSpeaking(false);
                return false;
              });
            }
            return true;
          } else if (jsonData.audio) {
            // Base64 encoded audio data
            const audioData = jsonData.audio;
            const audioBlob = base64ToBlob(audioData, 'audio/mpeg');
            const audioUrl = URL.createObjectURL(audioBlob);
            
            audioRef.current.src = audioUrl;
            audioRef.current.addEventListener('ended', () => {
              setSpeaking(false);
              URL.revokeObjectURL(audioUrl);
            });
            audioRef.current.addEventListener('error', (e) => {
              console.error('Audio playback error:', e);
              setSpeaking(false);
              URL.revokeObjectURL(audioUrl);
              throw new Error('Error playing audio from base64');
            });
            
            // Play the audio
            const playPromise = audioRef.current.play();
            if (playPromise) {
              playPromise.then(() => {
                console.log('Speechify audio playback started from base64');
              }).catch(error => {
                console.error('Speechify audio play promise rejected:', error);
                URL.revokeObjectURL(audioUrl);
                setSpeaking(false);
                return false;
              });
            }
            return true;
          } else {
            console.error("Speech endpoint returned no audio data:", jsonData);
          }
        } else {
          console.log("Speech endpoint failed with status:", speechResponse.status);
          const errorText = await speechResponse.text();
          console.error("Speech endpoint error:", errorText);
        }
      } catch (speechError) {
        console.error("Error calling speech endpoint:", speechError);
      }
      
      // If we got here, both API endpoints failed
      console.error('Both Speechify API endpoints failed');
      return false;
      
    } catch (error) {
      console.error('Error using Speechify API directly:', error);
      setSpeaking(false);
      return false;
    }
  };
  
  // Helper function to convert base64 to Blob
  const base64ToBlob = (base64, mimeType) => {
    const byteString = atob(base64);
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    
    for (let i = 0; i < byteString.length; i++) {
      ia[i] = byteString.charCodeAt(i);
    }
    
    return new Blob([ab], { type: mimeType });
  };

  // Modified speakWithBrowserTTS to handle text chunking better
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
        try {
          if (audioContextRef.current.state !== 'closed') {
            audioContextRef.current.close().catch(console.error);
          }
        } catch (error) {
          console.error('Error closing audio context:', error);
        }
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

  // Update the startNewInterview function to use a specific welcome message
  const startNewInterview = () => {
    setAiResponse('');
    setInterviewComplete(false);
    setConversationHistory([]);
    setError('');
    // Use the welcome message instead of generic "Start interview"
    setTimeout(() => {
      fetchTextAndVoiceResponse("Hello! Welcome to interview AI. Please state the occasion of ur interview and we shall proceed", selectedVoice);
    }, 100);
  };

  // Reset the interview
  const resetInterview = () => {
    setAiResponse('');
    setInterviewComplete(false);
    setConversationHistory([]);
    setError('');
  };

  // Enhanced toggleListening function
  const toggleListening = () => {
    // If interview is complete, reset and start a new one
    if (interviewComplete) {
      resetInterview();
      return;
    }
    
    // Clear any previous errors
    setError('');
    
    if (listening) {
      console.log('Stopping speech recognition');
      recognitionRef.current?.stop();
      setListening(false);
    } else {
      console.log('Initializing speech recognition');
      
      // Check browser support again to ensure it's still available
      const support = checkBrowserSupport();
      if (!support.speechRecognition) {
        return; // Error already set in checkBrowserSupport
      }
      
      try {
        const SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition;
        const recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      recognition.continuous = true; // Allow continuous listening

      recognition.onstart = () => {
        console.log('Speech recognition started');
          setAiResponse(''); // Clear previous response
          setError(''); // Clear any previous errors
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
          
          // Provide more helpful error messages
          switch (event.error) {
            case 'no-speech':
              setError('No speech was detected. Please try again and speak clearly.');
              break;
            case 'aborted':
              // This is a normal state when we stop listening intentionally
              break;
            case 'network':
              setError('Network error occurred. Please check your internet connection.');
              break;
            case 'not-allowed':
              setError('Speech recognition permission was denied. Please allow microphone access.');
              break;
            case 'service-not-allowed':
              setError('Speech recognition service is not allowed. Please try a different browser.');
              break;
            default:
              setError(`Speech recognition error: ${event.error}`);
          }
      };

      recognition.onend = () => {
        console.log('Speech recognition ended');
          setListening(false);
          
        // Ensure UI updates are triggered
        if (speechResultRef.current) {
            // Process the user's speech and get AI response with voice
            fetchTextAndVoiceResponse(speechResultRef.current, selectedVoice);
          speechResultRef.current = ''; // Clear the stored result
        }
      };

      recognitionRef.current = recognition;

      // Start recognition immediately
      recognition.start();
      setListening(true);
      } catch (err) {
        console.error('Error initializing speech recognition:', err);
        setError(`Could not initialize speech recognition: ${err.message}`);
      }
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
    const apiUrl = `${API_BASE_URL}/api/text`;
    
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

  // Enhanced fetchTextAndVoiceResponse to track conversation
  const fetchTextAndVoiceResponse = async (inputText, selectedVoice) => {
    setIsWaiting(true);
    setError(''); // Clear any previous errors
    setLoading(true);
    
    console.log(`Processing input: "${inputText.substring(0, 30)}..."`);
    
    try {
      // Use Gemini API directly or through proxy if needed
      let aiResponseText;
      
      // Try to use the backend API first
      try {
        // Make request to the text API to get AI's response
        const textResponse = await fetch(`${API_BASE_URL}/api/text`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: inputText
          }),
        });

        if (!textResponse.ok) {
          console.warn(`HTTP error on text request! status: ${textResponse.status}`);
          throw new Error(`HTTP error on text request! status: ${textResponse.status}`);
        }
        
        // Parse the JSON response
        const textData = await textResponse.json();
        
        if (!textData.response) {
          throw new Error('No response text received from API');
        }
        
        // Extract the AI's response text
        aiResponseText = textData.response;
      } catch (textApiError) {
        console.error("Error using backend text API:", textApiError);
        
        // Fallback text - this is just a placeholder since we can't generate AI text without the backend
        aiResponseText = "I'm currently having trouble connecting to my response system. However, I'm still able to help you practice interviews. What kind of interview are you preparing for?";
      }
      
      // Update the UI with the AI's text response
      setAiResponse(aiResponseText);
      
      // Update conversation history
      setConversationHistory(prev => [
        ...prev, 
        { 
          role: 'user', 
          content: inputText 
        },
        { 
          role: 'assistant', 
          content: aiResponseText 
        }
      ]);
      
      // Check if this is an interview completion
      if (aiResponseText.toLowerCase().includes('thank you for your time') ||
          aiResponseText.toLowerCase().includes('this concludes our interview') ||
          aiResponseText.includes('interview is complete')) {
        console.log('Interview appears to be complete');
        setInterviewComplete(true);
      }
      
      // Now use Speechify API directly for TTS - this is the key part we're fixing
      // Using direct Speechify API call with the provided API key
      console.log("Using Speechify API directly with key:", SPEECHIFY_API_KEY.substring(0, 5) + "..." + SPEECHIFY_API_KEY.substring(SPEECHIFY_API_KEY.length - 5));
      
      const speechifySuccess = await speakWithSpeechifyDirect(aiResponseText, selectedVoice);
      
      if (speechifySuccess) {
        console.log('Successfully used Speechify API directly');
        setIsWaiting(false);
        setLoading(false);
        return;
      }
      
      // If Speechify failed, try VoiceRSS directly
      const voiceRssSuccess = await speakWithVoiceRSS(aiResponseText, selectedVoice);
      
      // If both direct API calls fail, fall back to proxy or browser TTS
      if (!speechifySuccess && !voiceRssSuccess) {
        console.log('Direct API calls failed, falling back to proxy');
        speakWithSpeechify(aiResponseText, selectedVoice);
      }
      
      setIsWaiting(false);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching text response:', error);
      setError(`Error getting AI response: ${error.message}`);
      setIsWaiting(false);
      setLoading(false);
    }
  };

  // Direct call to VoiceRSS API (using the SDK included in public/index.html)
  const speakWithVoiceRSS = async (text, voiceId = 'en-us') => {
    console.log(`Speaking with VoiceRSS, voice: ${voiceId}, text length: ${text.length}`);
    
    if (!text) {
      console.error('No text provided for speech');
      return false;
    }
    
    // Map Speechify voice IDs to VoiceRSS voices
    const voiceMap = {
      'belinda': 'en-us',
      'matthew': 'en-us',
      'aria': 'en-us',
      'ryan': 'en-us',
      'joseph': 'en-us',
      'tom': 'en-gb',
      'henry': 'en-gb',
      'jane': 'en-us'
    };
    
    // Get the mapped voice or default to en-us
    const mappedVoice = voiceMap[voiceId] || 'en-us';
    
    try {
      setSpeaking(true);
      setError('');
      
      // Check if VoiceRSS SDK is available
      if (typeof VoiceRSS === 'undefined') {
        console.error('VoiceRSS SDK not available');
        return false;
      }
      
      console.log(`Using VoiceRSS with voice: ${mappedVoice}`);
      
      // The VoiceRSS SDK is already set up to play audio directly
      VoiceRSS.speech({
        key: '25b4ce640dcf4aaf8ce3af6bd9b2c3b9', // VoiceRSS API key
        src: text,
        hl: mappedVoice,
        v: 'Mary', // Voice name
        r: 0, // Rate
        c: 'mp3', // Codec
        f: '44khz_16bit_stereo', // Format
        ssml: false,
        b64: false,
        callback: function(error) {
          if (error) {
            console.error('VoiceRSS error:', error);
            setSpeaking(false);
            return false;
          } else {
            // Success, speech is playing
            console.log('VoiceRSS speech playing');
            
            // Since VoiceRSS doesn't provide a way to know when audio completes,
            // we'll use a timeout based on text length
            const estimatedDuration = Math.max(2000, text.length * 80); // Rough estimate: 80ms per character
            setTimeout(() => {
              setSpeaking(false);
            }, estimatedDuration);
            
            return true;
          }
        }
      });
      
      return true;
      
    } catch (error) {
      console.error('Error using VoiceRSS:', error);
      setSpeaking(false);
      return false;
    }
  };

  // Update the fetchVoiceResponse function to use Speechify directly
  const fetchVoiceResponse = async (text) => {
    // Try to use Speechify API directly first
    const speechifySuccess = await speakWithSpeechifyDirect(text, selectedVoice);
    
    if (speechifySuccess) {
      console.log('Successfully used Speechify API directly');
      return;
    }
    
    // If Speechify failed, try VoiceRSS directly
    const voiceRssSuccess = await speakWithVoiceRSS(text, selectedVoice);
    
    // If both direct API calls fail, fall back to proxy or browser TTS
    if (!speechifySuccess && !voiceRssSuccess) {
      console.log('Direct API calls failed, falling back to proxy');
      speakWithSpeechify(text, selectedVoice);
    }
  };

  return (
    <div className="App">
      <div className="background-square"></div>
      
      {/* Navigation Bar */}
      <nav className="navbar">
        <div className="navbar-brand">🧠 Forge Future</div>
        <div className="navbar-links">
          <Link to="/essay-aid" className="nav-link">College Essay Aid</Link>
          <Link to="/opportunities" className="nav-link">Internship/Job Opportunities</Link>
          <Link to="/" className="nav-link active">Interview AI</Link>
      </div>
      </nav>
      
      <div className="container">
        <div className="header">
          <h1 style={{ color: '#7e57c2' }}>Interview AI</h1>
          <p>Enhance your interview skills with real-time feedback from AI</p>
        </div>
        <div className={`blob ${speaking ? 'speaking' : ''}`}>
          <div className="blob-inner">
            {/* AI response text removed as requested */}
          </div>
        </div>
        
        {/* Display voice options and start button */}
        <div className="voice-options">
          <div className="voice-selector">
            <select
              value={selectedVoice}
              onChange={(e) => setSelectedVoice(e.target.value)}
              disabled={listening || speaking || isWaiting}
            >
              {VOICE_OPTIONS.map(voice => (
                <option key={voice.id} value={voice.id}>
                  {voice.name}
                </option>
              ))}
            </select>
          </div>
          
          <label>
            <input
              type="checkbox"
              checked={useVoiceApi}
              onChange={() => setUseVoiceApi(!useVoiceApi)}
              disabled={listening || speaking || isWaiting}
            />
            Use Voice Output
          </label>
        </div>

        {/* Move Start Interview button here - right after voice options */}
        <button 
          className="start-interview-button"
          onClick={!interviewComplete ? startNewInterview : resetInterview}
          disabled={listening || speaking || isWaiting}
        >
          {interviewComplete ? (
            <>
              <span className="restart-icon">↺</span> Restart Interview
            </>
          ) : (
            'Start Interview'
          )}
        </button>

        {/* Only show mic button if the interview has started */}
        {conversationHistory.length > 0 && (
          <button 
            className={`mic-button ${listening ? 'listening' : ''} ${processingAudio ? 'processing' : ''} ${interviewComplete ? 'complete' : ''}`}
            onClick={interviewComplete ? startNewInterview : toggleListening} 
            disabled={speaking || isWaiting || processingAudio}
            title={interviewComplete ? "Start new interview" : 
                  (browserSupport.speechRecognition ? "Click to speak" : 
                  "Speech recognition not supported in this browser")}
          >
            <div className={`mic-icon ${interviewComplete ? 'restart-icon' : ''}`}></div>
          </button>
        )}

        {isWaiting && <div className="waiting-indicator"></div>}
        {processingAudio && <div className="processing-indicator">Processing audio...</div>}
        
        <div className="status-text">
          {interviewComplete ? 'Interview complete! Click to start a new one' :
           listening ? 'Listening...' : 
           speaking ? 'Speaking...' : 
           processingAudio ? 'Processing...' : 
           conversationHistory.length === 0 ? 'Click to start interview' : 'Click to speak'}
        </div>
        
        {/* Display error message if present */}
        {error && (
          <div className="error-message">
            <p>{error}</p>
          </div>
        )}

        {/* Browser compatibility warning */}
        {!browserSupport.speechRecognition && (
          <div className="compatibility-warning">
            <p>Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari for the best experience.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;