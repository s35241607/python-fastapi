# FastAPI Backend 專案

一個使用 FastAPI、SQLAlchemy 和 PostgreSQL 的現代化後端 API 專案。

## 🚀 快速開始

### 1. 環境需求

- Python 3.11+
- PostgreSQL 12+
- uv (Python 套件管理工具)

### 2. 安裝 uv

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用 pip
pip install uv
```

### 3. 專案設定

```bash
# 1. 進入專案目錄
cd backend

# 2. 安裝依賴
uv sync

# 3. 安裝開發工具
uv sync --group dev

# 4. 複製環境變數檔案
copy .env.example .env

# 5. 編輯 .env 檔案，設定你的資料庫連接
# DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/your_database
```

### 4. 資料庫設定

```bash
# 確保 PostgreSQL 服務正在運行
# 創建資料庫 (如果尚未存在)
createdb your_database_name

# 測試資料庫連接
uv run python -c "
import asyncio
from app.database import engine
from sqlalchemy import text

async def test():
    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT 1'))
        print('✅ 資料庫連接成功!')

asyncio.run(test())
"
```

### 5. 啟動開發伺服器

```bash
# 方法 1: 使用 uv (推薦)
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 方法 2: 使用 VS Code F5 調試
# 在 VS Code 中按 F5，選擇 "Python: FastAPI Simple Debug"
```

### 6. 驗證安裝

開啟瀏覽器訪問：

- **API 根路徑**: http://127.0.0.1:8000
- **API 文檔**: http://127.0.0.1:8000/docs
- **ReDoc 文檔**: http://127.0.0.1:8000/redoc

## 🔧 開發工具

### VS Code 自動格式化

專案已配置自動格式化功能：

- **Black**: Python 程式碼格式化
- **isort**: Import 語句排序
- **Flake8**: 程式碼檢查

**使用方式**：

- 儲存時自動格式化 (`Ctrl+S`)
- 手動格式化 (`Shift+Alt+F`)
- 整理 Import (`Shift+Alt+O`)

### 手動格式化指令

```bash
# 格式化所有 Python 檔案
uv run black app/

# 排序 Import
uv run isort app/

# 程式碼檢查
uv run flake8 app/

# 類型檢查
uv run mypy app/
```

## 🏭 生產環境部署

### 1. 環境變數配置

```bash
# 複製生產環境配置
copy .env.production .env

# 編輯 .env 檔案，設定生產環境參數
```

### 2. 重要的生產環境設定

編輯 `.env` 檔案：

```bash
# 環境類型
ENVIRONMENT=production

# 資料庫 (使用生產資料庫)
DATABASE_URL=postgresql+asyncpg://prod_user:secure_password@prod-db-host:5432/prod_database
DB_ECHO=false

# 安全設定 (必須使用強密鑰)
SECRET_KEY=your-super-secure-production-secret-key-at-least-64-characters-long
ACCESS_TOKEN_EXPIRE_MINUTES=15

# 應用設定
APP_NAME=FastAPI Backend
LOG_LEVEL=WARNING

# 關閉調試功能
DEBUG=false
```

### 3. 生產環境啟動

```bash
# 生產環境啟動指令
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 或使用 Gunicorn (推薦)
uv run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 4. 生產環境安全檢查清單

- ✅ **強密鑰**: SECRET_KEY 至少 64 字元
- ✅ **HTTPS**: 使用 SSL/TLS 加密
- ✅ **CORS**: 限制允許的來源網域
- ✅ **API 文檔**: 生產環境會自動隱藏
- ✅ **日誌等級**: 設為 WARNING 或 ERROR
- ✅ **資料庫**: 使用生產資料庫
- ✅ **環境變數**: 不要在程式碼中硬編碼敏感資訊

## 🧪 測試

```bash
# 執行所有測試
uv run pytest

# 執行特定測試檔案
uv run pytest tests/test_users.py

# 執行測試並顯示覆蓋率
uv run pytest --cov=app tests/
```

## 📁 專案結構

```
backend/
├── app/
│   ├── core/           # 核心配置
│   │   ├── config.py   # 應用配置
│   │   └── ...
│   ├── models/         # 資料庫模型
│   ├── routers/        # API 路由
│   ├── schemas/        # Pydantic 模型
│   ├── database.py     # 資料庫連接
│   └── main.py         # FastAPI 應用入口
├── tests/              # 測試檔案
├── .env.example        # 開發環境範例
├── .env.production     # 生產環境範例
├── pyproject.toml      # 專案配置
└── README.md           # 專案說明
```

## 🔍 檢查當前環境

```bash
# 檢查環境設定
uv run python -c "
from app.core.config import settings
print(f'🌍 Environment: {settings.DEBUG and \"Development\" or \"Production\"}')
print(f'🐛 Debug Mode: {settings.DEBUG}')
print(f'📊 DB Echo: {settings.DB_ECHO}')
print(f'🔒 Secret Key Length: {len(settings.SECRET_KEY)} chars')
print(f'🌐 CORS Origins: {settings.ALLOWED_ORIGINS}')
"
```

## 🆘 常見問題

### Q: 無法連接資料庫

**A**: 檢查 PostgreSQL 服務是否運行，資料庫 URL 是否正確

### Q: VS Code 自動格式化不工作

**A**: 確保安裝了必要的擴充套件：Python、Black Formatter、isort

### Q: F5 調試無法啟動

**A**: 檢查 Python 解釋器路徑是否正確指向虛擬環境

### Q: 生產環境 API 文檔無法訪問

**A**: 這是正常的，生產環境會自動隱藏 API 文檔以提高安全性

## 📞 支援

如有問題，請檢查：

1. 環境變數設定是否正確
2. 資料庫連接是否正常
3. 依賴套件是否完整安裝
4. Python 版本是否符合需求 (3.11+)
