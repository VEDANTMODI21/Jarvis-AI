from flask import Flask, request, jsonify
import os
import webbrowser
import pyttsx3
import datetime

app = Flask(__name__)

engine = pyttsx3.init()

def say(text):
    engine.say(text)
    engine.runAndWait()

@app.route("/process", methods=["POST"])
def process():
    data = request.json
    command = data.get("command", "").lower()

    if "time" in command:
        time_now = datetime.datetime.now().strftime("%H:%M")
        response = f"The current time is {time_now}"
    elif "hello" in command:
        response = "Hello! How can I assist you today?"
    elif "open youtube" in command:
        response = "Opening YouTube..."
        webbrowser.open("https://www.youtube.com")
    else:
        response = "Sorry, I didn't understand that."

    say(response)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
