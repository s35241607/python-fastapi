@echo off
echo 🧪 Starting FastAPI in TESTING mode...
copy .env.testing .env
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
