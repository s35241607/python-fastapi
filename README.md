# 全端開發專案

現代化的前後端分離架構專案，使用最新的技術棧構建。

## 🏗️ 技術棧

### 前端

- **框架**: Vue 3 + TypeScript
- **構建工具**: Vite
- **狀態管理**: Pinia
- **HTTP 客戶端**: Axios
- **路由**: Vue Router

### 後端

- **框架**: FastAPI + Python 3.11+
- **ORM**: SQLAlchemy (異步)
- **資料庫**: PostgreSQL 16
- **套件管理**: uv
- **API 文檔**: Swagger/OpenAPI

### 開發工具

- **容器化**: Docker + Docker Compose
- **IDE**: VS Code (支援調試)
- **程式碼格式化**: Black, Prettier, ESLint
- **版本控制**: Git

## 📁 專案結構

```
project/
├── frontend/              # Vue3 前端應用
│   ├── src/              # 前端源碼
│   ├── package.json      # 前端依賴
│   └── README.md         # 前端開發指南
├── backend/              # FastAPI 後端應用
│   ├── app/              # 後端源碼
│   ├── pyproject.toml    # 後端依賴
│   └── README.md         # 後端開發指南
├── docs/                 # 專案文檔
├── .vscode/              # VS Code 配置
├── docker-compose.yml    # Docker 編排
└── README.md            # 專案總覽 (本文件)
```

## 🚀 快速開始

### 前置需求

- **Node.js** 18+ (前端)
- **Python** 3.11+ (後端)
- **PostgreSQL** 12+ (資料庫)
- **uv** (Python 套件管理)
- **VS Code** (推薦 IDE)

### 🔧 開發環境設定

#### 1. 克隆專案

```bash
git clone <repository-url>
cd project
```

#### 2. 後端設定

```bash
cd backend
# 詳細步驟請參考 backend/README.md
uv sync
copy .env.example .env
# 編輯 .env 設定資料庫連接
uv run uvicorn app.main:app --reload
```

#### 3. 前端設定

```bash
cd frontend
# 詳細步驟請參考 frontend/README.md
npm install
npm run dev
```

### 🐳 Docker 快速啟動

```bash
# 啟動所有服務 (前端 + 後端 + 資料庫)
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 停止所有服務
docker-compose down
```

### 🐛 VS Code 調試模式

1. 在 VS Code 中開啟專案
2. 安裝推薦的擴充套件
3. 按 **F5** 選擇調試配置：
   - `Python: FastAPI Debug` - 後端調試
   - `Vue.js: Debug` - 前端調試
   - `Launch Full Stack` - 同時調試前後端

詳細調試說明請參考 [DEBUG_GUIDE.md](DEBUG_GUIDE.md)

## 🌐 服務端口

| 服務     | 開發環境                   | 生產環境              | 說明                    |
| -------- | -------------------------- | --------------------- | ----------------------- |
| 前端     | http://localhost:5173      | http://localhost:3000 | Vue.js 應用             |
| 後端 API | http://localhost:8000      | http://localhost:8000 | FastAPI 服務            |
| API 文檔 | http://localhost:8000/docs | -                     | Swagger UI (僅開發環境) |
| 資料庫   | localhost:5432             | -                     | PostgreSQL              |

## 📚 詳細文檔

### 開發指南

- **[前端開發指南](frontend/README.md)** - Vue.js 前端開發詳細說明
- **[後端開發指南](backend/README.md)** - FastAPI 後端開發詳細說明
- **[調試指南](DEBUG_GUIDE.md)** - VS Code 調試配置說明

### 技術規範

- **[API 規範](docs/api-standards.md)** - RESTful API 設計規範
- **[程式碼規範](docs/code-style.md)** - 程式碼風格指南
- **[資料庫規範](docs/database-standards.md)** - 資料庫設計規範

## 🔄 開發工作流程

### 日常開發

1. **啟動開發環境**

   ```bash
   # 終端 1: 啟動後端
   cd backend && uv run uvicorn app.main:app --reload

   # 終端 2: 啟動前端
   cd frontend && npm run dev
   ```

2. **程式碼格式化**

   ```bash
   # 後端格式化
   cd backend && uv run black app/

   # 前端格式化
   cd frontend && npm run format
   ```

3. **執行測試**

   ```bash
   # 後端測試
   cd backend && uv run pytest

   # 前端測試 (如果有配置)
   cd frontend && npm run test
   ```

### 部署到生產環境

1. **後端部署** - 參考 [backend/README.md](backend/README.md#生產環境部署)
2. **前端部署** - 參考 [frontend/README.md](frontend/README.md#部署)

## 🆘 常見問題

### 環境問題

- **Q**: 無法啟動後端服務
- **A**: 檢查 PostgreSQL 是否運行，資料庫連接設定是否正確

- **Q**: 前端無法連接後端 API
- **A**: 確認後端服務正在運行，檢查 CORS 設定

### 開發問題

- **Q**: VS Code 自動格式化不工作
- **A**: 確保安裝了推薦的擴充套件，檢查 Python 解釋器設定

- **Q**: 調試模式無法啟動
- **A**: 檢查 launch.json 配置，確認虛擬環境路徑正確

## 🤝 貢獻指南

1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📄 授權

本專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 檔案
