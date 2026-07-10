# Jarvis AI

A web-based AI voice assistant built with Flask. Ask for the time, weather, news, Wikipedia summaries, or just chat — Jarvis responds in text and speech. Data is persisted in a SQL database so history is available on any device.

## Features

- Voice and text chat interface
- Time, date, weather, and news commands
- Wikipedia summaries
- OpenAI-powered general chat (optional)
- Persistent conversation history
- Modern dark UI
- Deploys to Vercel

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
flask run
```

## Environment variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL/SQLite connection string | No (defaults to SQLite) |
| `OPENAI_API_KEY` | OpenAI API key for AI chat | No |
| `OPENWEATHER_API_KEY` | OpenWeather API key for weather | No |
| `NEWS_API_KEY` | NewsAPI key for news headlines | No |

## Deployment

The project is configured for zero-config deployment on Vercel. Set your secrets in the Vercel dashboard, then:

```bash
vercel --prod
```

## Project structure

- `app.py` — Flask backend and command processing
- `templates/index.html` — main UI
- `public/` — static assets (CSS, JS)
- `pyproject.toml` — project metadata and Vercel entrypoint
