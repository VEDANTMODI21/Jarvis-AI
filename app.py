import os
import re
import requests
from datetime import datetime

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import openai
from dotenv import load_dotenv

load_dotenv()

DEFAULT_HEADERS = {
    "User-Agent": "JarvisAI/1.0 (contact@example.com)"
}

app = Flask(__name__, static_folder="public", static_url_path="")

# Database
raw_database_url = os.getenv("DATABASE_URL", "sqlite:///jarvis.db")
if raw_database_url.startswith("postgres://"):
    raw_database_url = raw_database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = raw_database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}

db = SQLAlchemy(app)

# API keys from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(10), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def create_tables():
    try:
        with app.app_context():
            db.create_all()
    except Exception as exc:  # pragma: no cover
        app.logger.error("Could not create database tables: %s", exc)


create_tables()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Message is required"}), 400

    try:
        db.session.add(Message(role="user", content=message))
        db.session.commit()

        response = process_command(message)

        db.session.add(Message(role="bot", content=response))
        db.session.commit()

        return jsonify({"response": response})
    except Exception as exc:
        app.logger.exception("Error processing chat")
        return jsonify({"error": "Failed to process request"}), 500


@app.route("/api/history", methods=["GET"])
def get_history():
    try:
        messages = (
            Message.query.order_by(Message.created_at.desc())
            .limit(50)
            .all()
        )
        return jsonify(
            {
                "history": [
                    {
                        "id": m.id,
                        "role": m.role,
                        "content": m.content,
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                    }
                    for m in messages
                ]
            }
        )
    except Exception as exc:
        app.logger.exception("Error loading history")
        return jsonify({"error": "Failed to load history"}), 500


@app.route("/api/history", methods=["DELETE"])
def clear_history():
    try:
        Message.query.delete()
        db.session.commit()
        return jsonify({"ok": True})
    except Exception as exc:
        app.logger.exception("Error clearing history")
        return jsonify({"error": "Failed to clear history"}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})


def process_command(command: str) -> str:
    text = command.lower()

    if text in ("time", "what time is it", "current time") or "time" in text.split():
        return f"The time is {datetime.now().strftime('%I:%M %p')}."

    if text in ("date", "what date is it", "today's date") or "date" in text.split():
        return f"Today's date is {datetime.now().strftime('%B %d, %Y')}."

    if "your name" in text:
        return "I am Jarvis, your AI assistant."

    if "how are you" in text:
        return "I'm doing great, thank you for asking!"

    if text.startswith("weather") or " weather" in text or "weather " in text:
        return get_weather(text)

    if "news" in text:
        return get_news()

    if "wikipedia" in text:
        return get_wikipedia_summary(text)

    if text.startswith("open "):
        return open_website(text)

    if text.startswith("ask openai") or text.startswith("ask ai"):
        prompt = re.sub(r"^(ask\s+(openai|ai)\s*)", "", command, flags=re.IGNORECASE).strip()
        return ask_openai(prompt or "Hello")

    # Fallback to OpenAI when available; otherwise DuckDuckGo.
    if openai_client:
        return ask_openai(command)

    return get_duckduckgo_answer(command)


def get_weather(command: str) -> str:
    if not OPENWEATHER_API_KEY:
        return "OpenWeather API key is not configured."

    city = extract_city(command)
    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    )
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
        data = response.json()
        if data.get("main"):
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            return f"The weather in {city.title()} is {desc} with a temperature of {temp}°C."
        if data.get("message"):
            return f"Weather: {data['message']}."
        return "Could not fetch weather details."
    except requests.RequestException as exc:
        app.logger.error("Weather API error: %s", exc)
        return "Weather service is currently unavailable."


def extract_city(command: str) -> str:
    match = re.search(r"weather(?:\s+(?:in|at|for))?\s+([a-zA-Z\s]+)", command, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r"(?:in|at|for)\s+([a-zA-Z\s]+)$", command, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Delhi"


def get_news() -> str:
    if not NEWS_API_KEY:
        return "News API key is not configured."

    url = "https://newsapi.org/v2/top-headlines"
    params = {"country": "in", "apiKey": NEWS_API_KEY, "pageSize": 5}
    try:
        response = requests.get(url, params=params, headers=DEFAULT_HEADERS, timeout=10)
        data = response.json()
        articles = data.get("articles", [])
        if articles:
            headlines = [f"- {a['title']}" for a in articles if a.get("title")]
            return "Here are the top news headlines:\n" + "\n".join(headlines)
        return "No news found."
    except requests.RequestException as exc:
        app.logger.error("News API error: %s", exc)
        return "News service is currently unavailable."


def get_wikipedia_summary(command: str) -> str:
    query = re.sub(r"wikipedia", "", command, flags=re.IGNORECASE).strip()
    if not query:
        return "Please tell me what to search for on Wikipedia."

    # Try a direct title match first; fall back to search if it fails.
    try:
        summary_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        response = requests.get(
            summary_url + requests.utils.quote(query),
            headers=DEFAULT_HEADERS,
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("extract"):
                return data["extract"]

        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 1,
        }
        response = requests.get(search_url, params=search_params, headers=DEFAULT_HEADERS, timeout=10)
        data = response.json()
        results = data.get("query", {}).get("search", [])
        if results:
            title = results[0]["title"]
            response = requests.get(
                summary_url + requests.utils.quote(title),
                headers=DEFAULT_HEADERS,
                timeout=10,
            )
            if response.status_code == 200:
                summary = response.json().get("extract")
                if summary:
                    return summary

        return "Sorry, I couldn't find anything on Wikipedia."
    except requests.RequestException as exc:
        app.logger.error("Wikipedia API error: %s", exc)
        return "Wikipedia service is currently unavailable."


def open_website(command: str) -> str:
    text = command.lower()
    sites = {
        "youtube": "https://www.youtube.com",
        "instagram": "https://www.instagram.com",
        "google": "https://www.google.com",
        "facebook": "https://www.facebook.com",
        "twitter": "https://www.twitter.com",
        "x": "https://www.x.com",
        "github": "https://www.github.com",
        "linkedin": "https://www.linkedin.com",
    }
    for name, url in sites.items():
        if name in text:
            return f"Opening {name.title()}: {url}"

    match = re.search(r"open\s+(.+)", text)
    if match:
        site = match.group(1).strip().replace(" ", "")
        return f"Opening https://{site}.com"
    return "I don't know which site to open."


def ask_openai(prompt: str) -> str:
    if not openai_client:
        return "OpenAI API key is not configured."

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are Jarvis, a helpful AI assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=256,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        app.logger.error("OpenAI API error: %s", exc)
        return "Sorry, I couldn't process your request with OpenAI."


def get_duckduckgo_answer(query: str) -> str:
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
    try:
        response = requests.get(url, params=params, headers=DEFAULT_HEADERS, timeout=10)
        if response.status_code in (200, 202):
            data = response.json()
            abstract = data.get("AbstractText", "") or data.get("Abstract", "")
            if abstract:
                return abstract
            related = data.get("RelatedTopics", [])
            if related:
                first = related[0]
                if isinstance(first, dict) and first.get("Text"):
                    return first["Text"]
                if isinstance(first, dict) and first.get("Topics"):
                    return first["Topics"][0].get("Text", "Sorry, I couldn't find any information on that.")
        return "Sorry, I couldn't find any information on that."
    except requests.RequestException as exc:
        app.logger.error("DuckDuckGo API error: %s", exc)
        return "Sorry, I encountered an error processing your request."


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
