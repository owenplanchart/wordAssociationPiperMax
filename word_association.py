import os
import requests
import subprocess
import speech_recognition as sr
from pynput import keyboard  # For cross-platform key detection

# Function to fetch word associations from Datamuse API
def get_associated_words(word, max_words=10):
    """Fetch word associations using Datamuse API."""
    api_url = f"https://api.datamuse.com/words?ml={word}&max={max_words}"
    response = requests.get(api_url)
    
    if response.status_code == 200:
        results = response.json()
        associated_words = [entry['word'] for entry in results]
        return associated_words
    else:
        print("Error: Could not fetch data.")
        return []

def speak_words(words):
    """Speak a list of words aloud using Piper."""
    try:
        # Join the words into one sentence.
        text = " ".join(words)
        # Define the path to your Piper model.
        model_path = "modules/piper/models/en_US-libritts_r-medium.onnx"
        # Build the command to generate the WAV file.
        command = f'echo "{text}" | piper --model {model_path} > output.wav'
        
        # Copy the current environment and add DYLD_LIBRARY_PATH.
        env = os.environ.copy()
        # Set this path to where libespeak-ng.dylib is located.
        env["DYLD_LIBRARY_PATH"] = "/Users/owen/Developer/Python/myPiperTTS/modules/piper/pp/install/lib:" + env.get("DYLD_LIBRARY_PATH", "")
        
        # Run the command with the modified environment.
        subprocess.run(command, shell=True, check=True, env=env)
        # Play the generated audio file using afplay.
        subprocess.run(["afplay", "output.wav"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Piper error: {e}")

# Function to listen to the microphone and recognize speech
def listen_to_microphone():
    """Listen to the microphone and return recognized speech."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening... Speak now!")
        try:
            audio = recognizer.listen(source, timeout=5)
            recognized_text = recognizer.recognize_google(audio)
            print(f"You said: {recognized_text}")
            return recognized_text
        except sr.UnknownValueError:
            print("Sorry, I did not understand what you said.")
        except sr.RequestError:
            print("Could not request results. Please check your internet connection.")
        except sr.WaitTimeoutError:
            print("Listening timed out. Try again.")
        return None

# Main logic using pynput for key control
def main():
    print("Word Association Tool with Microphone Activation:")
    print("- Hold the SPACE bar to activate the microphone.")
    print("- Press 'q' to exit.\n")
    
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    global listening, exit_program
    listening = False
    exit_program = False

    while not exit_program:
        if listening:
            word = listen_to_microphone()
            if word:
                associations = get_associated_words(word)
                if associations:
                    print("\nAssociated words:")
                    for idx, associated_word in enumerate(associations, 1):
                        print(f"{idx}. {associated_word}")
                    speak_words(associations)  # Speak the associated words using Piper
                else:
                    print("No associations found.")
            listening = False  # Stop listening until space bar is pressed again

def on_press(key):
    """Handles key presses."""
    global listening, exit_program
    try:
        if key == keyboard.Key.space:
            if not listening:
                print("\nSpace bar detected! Activating microphone...")
                listening = True
        elif key.char == 'q':
            print("Exiting the program. Goodbye!")
            exit_program = True
    except AttributeError:
        pass

def on_release(key):
    """Handles key releases."""
    global listening
    if key == keyboard.Key.space:
        listening = False

if __name__ == "__main__":
    main()

