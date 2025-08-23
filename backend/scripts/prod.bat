@echo off
echo 🏭 Starting FastAPI in PRODUCTION mode...
if not exist .env.production (
    echo ❌ .env.production file not found!
    echo Please create .env.production with production settings
    exit /b 1
)
copy .env.production .env
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
