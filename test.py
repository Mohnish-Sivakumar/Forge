import google.generativeai as genai
import pyttsx3
import speech_recognition as sr

# Configure Gemini API
genai.configure(api_key="AIzaSyDrxMRoQ-Knm7gM_6YNHAiPhXoC6HN09S4")  # Replace with your API key
model = genai.GenerativeModel('gemini-1.5-flash')

# Configure pyttsx3
engine = pyttsx3.init()

# Configure speech_recognition
recognizer = sr.Recognizer()

def get_gemini_response(prompt):
    """Gets a response from the Gemini API."""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error getting Gemini response: {e}")
        return "Sorry, I encountered an error."

def speak(text):
    """Speaks the given text using pyttsx3."""
    engine.say(text)
    engine.runAndWait()

def listen():
    """Listens for voice input and returns the text."""
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)  # Reduce noise
        audio = recognizer.listen(source)

    try:
        print("Recognizing...")
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I could not understand.")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
        return ""

def voice_assistant():
    """Main voice assistant loop."""
    print("Voice Assistant started. Say 'exit' to quit.")
    while True:
        user_input = listen()
        if user_input.lower() == "exit":
            break
        if user_input: #prevents errors from empty strings.
            response = get_gemini_response(user_input)
            print("Assistant:", response)
            speak(response)

if __name__ == "__main__":
    voice_assistant()