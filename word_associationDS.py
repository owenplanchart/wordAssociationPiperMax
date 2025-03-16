import os
import time
import requests
import subprocess
import speech_recognition as sr
from pynput import keyboard

# Configuration
MODEL_PATH = os.path.abspath("modules/piper/models/en_US-libritts_r-medium.onnx")
LIBRARY_PATH = "/Users/owen/Developer/Python/myPiperTTS/modules/piper/pp/install/lib"
OUTPUT_DIR = os.path.abspath("generated_audio")
TRIGGER_FILE = os.path.abspath("latest_wav.txt")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_associated_words(word, max_words=10):
    """Fetch word associations using Datamuse API."""
    try:
        response = requests.get(
            "https://api.datamuse.com/words",
            params={"ml": word, "max": max_words}
        )
        response.raise_for_status()
        return [entry['word'] for entry in response.json()]
    except Exception as e:
        print(f"API Error: {e}")
        return []

def generate_audio(text):
    """Generate audio file using Piper and return path to file."""
    try:
        # Create unique filename
        timestamp = int(time.time() * 1000)
        filename = f"output_{timestamp}.wav"
        output_path = os.path.join(OUTPUT_DIR, filename)

        # Configure environment for Piper
        env = os.environ.copy()
        env["DYLD_LIBRARY_PATH"] = f"{LIBRARY_PATH}:{env.get('DYLD_LIBRARY_PATH', '')}"

        # Generate audio with Piper
        with open(output_path, "wb") as f:
            piper_process = subprocess.Popen(
                ["piper", "--model", MODEL_PATH],
                stdin=subprocess.PIPE,
                stdout=f,
                env=env,
                text=True
            )
            piper_process.communicate(input=text)
        
        # Update trigger file for Max
        with open(TRIGGER_FILE, "w") as f:
            f.write(output_path)
            
        return output_path
    except Exception as e:
        print(f"Audio Generation Error: {e}")
        return None

def speak_words(words):
    """Process and speak associated words."""
    if not words:
        return
        
    text = " ".join(words)
    print(f"Generating speech for: {text}")
    audio_path = generate_audio(text)
    
    if audio_path:
        print(f"Audio ready at: {audio_path}")
        # Optional: For local testing
        # subprocess.run(["afplay", audio_path])

def listen_to_microphone():
    """Listen to microphone and return recognized speech."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening... Speak now!")
        try:
            audio = recognizer.listen(source, timeout=5)
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            print("Speech not understood")
        except Exception as e:
            print(f"Recognition Error: {e}")
        return None

class AudioApp:
    """Main application controller"""
    def __init__(self):
        self.listening = False
        self.exit_program = False
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        
    def on_press(self, key):
        try:
            if key == keyboard.Key.space and not self.listening:
                print("\nMicrophone activated")
                self.listening = True
            elif hasattr(key, 'char') and key.char == 'q':
                print("Exiting...")
                self.exit_program = True
        except Exception as e:
            print(f"Key Error: {e}")

    def on_release(self, key):
        if key == keyboard.Key.space:
            self.listening = False

    def run(self):
        print("Word Association Tool with Max/MSP Integration")
        print("- Hold SPACE to speak")
        print("- Press Q to quit\n")
        
        self.listener.start()
        
        while not self.exit_program:
            if self.listening:
                if word := listen_to_microphone():
                    if associations := get_associated_words(word):
                        print("\nAssociations:")
                        for i, w in enumerate(associations, 1):
                            print(f"{i}. {w}")
                        speak_words(associations)
                    else:
                        print("No associations found")
                self.listening = False

if __name__ == "__main__":
    app = AudioApp()
    app.run()