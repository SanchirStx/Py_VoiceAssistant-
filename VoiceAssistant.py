import speech_recognition as sr
import pyttsx3
import json
import os
import datetime
import webbrowser
import random
import re
import wikipedia

engine = pyttsx3.init()
MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory.json")

def speak(text):
    engine.say(text)
    engine.runAndWait()
    print(text)
    return text

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Warning: memory file corrupted — starting with empty memory.")
            return {}
    return {}

def save_memory(mem):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(mem, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Failed to save memory:", e)

# load memory on startup
memory = load_memory()

def listen():
    reconizing = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        reconizing.adjust_for_ambient_noise(source)
        try:
            audio = reconizing.listen(source, timeout=5)
            command = reconizing.recognize_google(audio).lower()
            print(f"You said: '{command}'")
            return command
        except sr.WaitTimeoutError:
            print("No speech detected.")
            return ""
        except sr.UnknownValueError:
            print("Sorry, I did not understand that.")
            return ""
        except sr.RequestError as e:
            print(f"Error with speech recognition: {e}")
            return ""

def _now_iso():
    return datetime.datetime.utcnow().isoformat()

def process_command(command):
    command = command.lower()

  
    if 'hello' in command:
        speak("Hello! How can I assist you today?")
    elif 'time' in command:
        now = datetime.datetime.now().strftime("%H:%M")
        speak(f"The current time is {now}")
    elif 'date' in command:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        speak(f"Today's date is {today}")
    elif 'open youtube' in command:
        webbrowser.open("https://www.youtube.com")
        speak("Opening YouTube.")

        memory.setdefault("last", {})["last_opened"] = "youtube"
        save_memory(memory)
    elif 'open google' in command:
        webbrowser.open("https://www.google.com")
        speak("Opening Google.")
        memory.setdefault("last", {})["last_opened"] = "google"
        save_memory(memory)

    elif 'search ' in command:
        query = command.split("search ", 1)[1]
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        speak(f"Searching for {query} on Google.")
        memory.setdefault("last", {})["last_search"] = query
        save_memory(memory)
    
    elif 'what is ' in command or "who is " in command or "tell me about " in command:
        topic = command.split("what is ", 1)[-1].split("who is ", 1)[-1].split("tell me about ", 1)[-1]
        try:
            summary = wikipedia.summary(topic, sentences=2)
            speak(summary)
            memory.setdefault("last", {})["last_wikipedia"] = topic
            save_memory(memory)
        except wikipedia.DisambiguationError as e:
            speak(f"There are multiple entries for {topic}. Please be more specific.")
        except wikipedia.PageError:
            speak(f"Sorry, I couldn't find any information on {topic}.")
        except Exception as e:
            speak(f"An error occurred while searching Wikipedia: {e}")

    elif 'joke' in command:
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "Why don't programmers like nature? It has too many bugs."
        ]
        joke = random.choice(jokes)
        speak(joke)
        memory.setdefault("counters", {})
        memory["counters"]["jokes"] = memory["counters"].get("jokes", 0) + 1
        memory.setdefault("last", {})["last_joke"] = joke
        save_memory(memory)

    elif 'remember my name is' in command or "remember my name's" in command:
        m = re.search(r"remember (?:my name is|my name's)\s+([a-zA-Z\s]+)", command)
        if m:
            name = m.group(1).strip().split(" and ")[0]  # Stop at "and" if present
            memory["name"] = name
            save_memory(memory)
            speak(f"Okay, I'll remember that your name is {name}.")
        else:
            speak("I couldn't detect a name, please try again.")

    elif command.startswith("remember ") or "remember that " in command:
        note = command
        note = note.replace("remember that", "", 1).replace("remember", "", 1).strip()
        if note:
            memory.setdefault("notes", []).append({"text": note, "time": _now_iso()})
            save_memory(memory)
            speak("Got it — I've saved that to memory.")
        else:
            speak("What should I remember?")

    elif "what is my name" in command or "what's my name" in command or "who am i" in command:
        if "name" in memory:
            speak(f"Your name is {memory['name']}.")
        else:
            speak("I don't know your name yet. You can say 'remember my name is ...'.")

    # List saved notes
    elif 'list memories' in command or 'show notes' in command or 'what did i tell you to remember' in command:
        notes = memory.get("notes", [])
        if not notes:
            speak("You have no saved notes.")
        else:
            speak(f"You have {len(notes)} saved note(s). Here they are:")
            for i, n in enumerate(notes[-10:], 1): 
                txt = n.get("text", "")
                t = n.get("time", "")
                speak(f"{i}. {txt} (saved {t})")

    # Forget commands: "forget my name", "forget buy milk"
    elif 'forget my name' in command or 'forget name' in command:
        if "name" in memory:
            del memory["name"]
            save_memory(memory)
            speak("Okay — I've forgotten your name.")
        else:
            speak("I don't have a name saved.")

    elif command.startswith("forget "):
        target = command.replace("forget", "", 1).strip()
        notes = memory.get("notes", [])
        original_len = len(notes)
        notes = [n for n in notes if target not in n.get("text", "")]
        if len(notes) < original_len:
            memory["notes"] = notes
            save_memory(memory)
            speak(f"I've forgotten notes containing '{target}'.")
        else:
            speak(f"I couldn't find any notes containing '{target}'.")

    elif 'how many jokes' in command or 'jokes count' in command:
        count = memory.get("counters", {}).get("jokes", 0)
        speak(f"I have told you {count} joke(s) while memory is enabled.")

    elif 'shut down' in command or 'quit' in command or 'good bye' in command:
        speak("Shutting down. Goodbye!")
        return False

    else:
        speak("Sorry, I can't perform that action yet.")
    return True

def main():
    speak("Hello! I am your AI assistant. How can I help you today?")
    while True:
        command = listen()
        if command:
            if not process_command(command):
                break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        speak("Exiting. Goodbye!")
    except Exception as e:
        speak(f"An error occurred: {e}")
