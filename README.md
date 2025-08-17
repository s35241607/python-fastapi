# 全端開發專案

前後端分離架構專案，包含：

- 前端: Vite + Vue3 + TypeScript
- 後端: UV + Python + FastAPI + SQLAlchemy ORM
- 資料庫: PostgreSQL 16
- 開發環境: Docker + Docker Compose
- 支援 VS Code Debug

## 專案結構

```
project/
├── frontend/          # Vue3 前端
├── backend/           # FastAPI 後端
├── docker-compose.yml # Docker 編排
├── .vscode/          # VS Code 配置
└── README.md         # 專案說明
```

## 快速開始

### 🐛 Debug 模式 (推薦)

1. 在 VS Code 中打開專案
2. 按 **F5** 啟動 debug 模式
3. 選擇 "Python: FastAPI Debug" 配置
4. 訪問 http://127.0.0.1:8000 測試

詳細說明請參考 [DEBUG_GUIDE.md](DEBUG_GUIDE.md)

### 🐳 Docker 模式

```bash
docker-compose up -d
```

### 🔧 手動模式

1. 後端開發：

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

2. 前端開發：

```bash
cd frontend
npm install
npm run dev
```

## 服務端口

- 前端: http://localhost:5173
- 後端 API: http://localhost:8000
- PostgreSQL: localhost:5432
