from flask import Flask, render_template, request, jsonify
from datetime import datetime
import requests
import mysql.connector
import wikipedia
import os
import openai

app = Flask(__name__)

# Add your free API keys here
OPENWEATHER_API_KEY = "6f1d738593364ed5acd131020250405"
NEWS_API_KEY = "pub_8476072c0a05f125451fadaeeeaf6281c22f8"
OPENAI_API_KEY = "sk-abcdef1234567890abcdef1234567890abcdef12"

openai.api_key = OPENAI_API_KEY

# Database connection
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="password",
            database="ai_bot",
            port=3306
        )
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return None

# Save messages to the database
def save_message(user_query, bot_response):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        sql = "INSERT INTO messages_library (user_query, bot_response) VALUES (%s, %s)"
        values = (user_query, bot_response)
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()
    else:
        print("Database connection failed. Message not saved.")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    data = request.get_json()
    command = data.get("message", "").strip().lower()

    if "time" in command:
        now = datetime.now()
        response = "The time is " + now.strftime("%I:%M %p")

    elif "date" in command:
        now = datetime.now()
        response = "Today's date is " + now.strftime("%B %d, %Y")

    elif "your name" in command:
        response = "I am Jarvis, your AI assistant."

    elif "how are you" in command:
        response = "I'm doing great, thank you for asking!"

    elif "weather" in command:
        response = get_weather("Delhi")

    elif "news" in command:
        response = get_news()

    elif "wikipedia" in command:
        query = command.replace("wikipedia", "").strip()
        response = get_wikipedia_summary(query)

    elif "open youtube" in command:
        response = "Opening YouTube..."
        os.system("start https://www.youtube.com")

    elif "open instagram" in command:
        response = "Opening Instagram..."
        os.system("start https://www.instagram.com")

    elif "ask openai" in command:
        prompt = command.replace("ask openai", "").strip()
        response = ask_openai(prompt)

    else:
        response = get_duckduckgo_answer(command)

    save_message(command, response)
    return jsonify({"response": response})

@app.route("/history", methods=["GET"])
def get_history():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM messages_library ORDER BY timestamp DESC LIMIT 20")
        messages = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"history": messages})
    else:
        return jsonify({"error": "Failed to connect to the database"})

def get_duckduckgo_answer(query):
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_html": 1,
        "skip_disambig": 1
    }
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            data = res.json()
            abstract = data.get("AbstractText", "")
            if abstract:
                return abstract
            return "Sorry, I couldn't find any information on that."
        else:
            return "I'm sorry, I encountered an error fetching information."
    except Exception as e:
        print("DuckDuckGo API error:", e)
        return "I'm sorry, I encountered an error processing your request."

def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        res = requests.get(url)
        data = res.json()
        if data.get("main"):
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            return f"The weather in {city} is {desc} with {temp}°C temperature."
        return "Could not fetch weather details."
    except:
        return "Weather service is currently unavailable."

def get_news():
    url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
    try:
        res = requests.get(url)
        articles = res.json().get("articles", [])[:3]
        if articles:
            headlines = [f"- {a['title']}" for a in articles]
            return "Here are the top news headlines:\n" + "\n".join(headlines)
        return "No news found."
    except:
        return "News service is currently unavailable."

def get_wikipedia_summary(query):
    try:
        summary = wikipedia.summary(query, sentences=2)
        return summary
    except:
        return "Sorry, I couldn't find anything on Wikipedia."

def ask_openai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI API error:", e)
        return "Sorry, I couldn't process your request with OpenAI."

if __name__ == "__main__":
    app.run(debug=True)
