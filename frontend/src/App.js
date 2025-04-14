import React, { useState } from 'react';

function App() {
  const [listening, setListening] = useState(false);
  const [response, setResponse] = useState('');

  const startListening = () => {
    const recognition = new window.webkitSpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      const speechResult = event.results[0][0].transcript;
      console.log('Speech received: ' + speechResult);
      fetchResponse(speechResult);
    };

    recognition.onspeechend = () => {
      recognition.stop();
      setListening(false);
    };

    recognition.onerror = (event) => {
      console.error('Error occurred in recognition: ' + event.error);
      setListening(false);
    };

    recognition.start();
    setListening(true);
  };

  const fetchResponse = async (text) => {
    try {
      const response = await fetch('http://localhost:5000/api/voice', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const reader = response.body.getReader();
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();

      while (true) {
        const {done, value} = await reader.read();
        if (done) break;

        // Play each chunk as it arrives
        const audioBuffer = await audioContext.decodeAudioData(value.buffer);
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        source.start(0);
      }

    } catch (error) {
      console.error('Error fetching response:', error);
    }
  };

  const playAudio = (audioData) => {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    audioContext.decodeAudioData(audioData, (buffer) => {
      const source = audioContext.createBufferSource();
      source.buffer = buffer;
      source.connect(audioContext.destination);
      source.start(0);
    }, (error) => {
      console.error('Error decoding audio data:', error);
    });
  };

  const speak = (text) => {
    const utterance = new SpeechSynthesisUtterance(text);
    window.speechSynthesis.speak(utterance);
  };

  return (
    <div className="App">
      <h1>Voice Assistant</h1>
      <button onClick={startListening} disabled={listening}>
        {listening ? 'Listening...' : 'Start Listening'}
      </button>
      <p>Response: {response}</p>
    </div>
  );
}

export default App;