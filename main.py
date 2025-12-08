import speech_recognition as sr
import os
import webbrowser
import pyttsx3
import datetime
import time
import mysql.connector

# Initialize pyttsx3 engine
engine = pyttsx3.init()

# Connect to MySQL
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",         # change if your MySQL user is different
        password="&Wearegood100",  # change this to your actual password
        database="ai_bot"  # your database name
    )
    cursor = db.cursor()
    print("Database connected successfully.")
except mysql.connector.Error as err:
    print(f"Error connecting to database: {err}")
    exit()

# Speak function
def say(text):
    engine.say(text)
    engine.runAndWait()

# Save command to DB
def save_command(command):
    try:
        cursor.execute("INSERT INTO command_history (command) VALUES (%s)", (command,))
        db.commit()
        print("Command saved to database.")
    except mysql.connector.Error as err:
        print(f"Error saving command to database: {err}")

# Voice input
def takeCommand():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.energy_threshold = 400
        r.pause_threshold = 1
        r.adjust_for_ambient_noise(source, duration=1)

        try:
            audio = r.listen(source, timeout=5)
            print("Recognizing...")
            query = r.recognize_google(audio, language="en-in")
            print(f"User said: {query}")
            return query.lower()
        except sr.UnknownValueError:
            print("Could not understand. Please try again.")
            return None
        except sr.RequestError:
            print("Error with the speech recognition service. Please try again later.")
            return None

if __name__ == '__main__':
    say("Jarvis A.I is now active.")
    print("Say 'Jarvis' to activate.")

    listening = False
    last_command_time = time.time()

    while True:
        if time.time() - last_command_time > 30:
            say("No response detected. Sleeping now.")
            listening = False

        command = takeCommand()

        if command:
            if "jarvis stop" in command:
                say("Shutting down. Bye Sir!")
                break

            if not listening:
                if "jarvis start" in command or "jarvis" in command:
                    say("Hello Sir. I am listening now.")
                    listening = True
                    last_command_time = time.time()
                continue

            # Jarvis is actively listening now
            last_command_time = time.time()
            save_command(command)

            # Command handling
            if "open youtube" in command:
                say("Opening YouTube.")
                webbrowser.open("https://www.youtube.com")
            elif "open google" in command:
                say("Opening Google.")
                webbrowser.open("https://www.google.com")
            elif "open wikipedia" in command:
                say("Opening Wikipedia.")
                webbrowser.open("https://www.wikipedia.com")
            elif "open music" in command:
                music_path = "C:\\Users\\YourUsername\\Music\\your-song.mp3"
                if os.path.exists(music_path):
                    os.system(f'start {music_path}')
                    say("Playing your music.")
                else:
                    say("Sorry, I could not find the music file.")
            elif "time" in command:
                time_now = datetime.datetime.now().strftime("%H:%M")
                say(f"Sir, the time is {time_now}")
            else:
                say("I didn't understand that command, sir.")
