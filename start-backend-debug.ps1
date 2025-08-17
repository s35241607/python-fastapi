# 啟動後端 Debug 模式
Write-Host "啟動 FastAPI 後端 (Debug 模式)..." -ForegroundColor Green
Set-Location backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000