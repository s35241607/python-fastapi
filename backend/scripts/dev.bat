@echo off
echo 🚀 Starting FastAPI in DEVELOPMENT mode...
copy .env.example .env 2>nul
echo ENVIRONMENT=development >> .env
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
