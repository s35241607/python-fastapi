# Python-FastAPI Full-Stack Project

現代化的前後端分離架構專案，使用最新的技術棧構建。

> **📋 Complete Documentation Available**
> - **[📖 Project Documentation](docs/PROJECT_DOCUMENTATION.md)** - Comprehensive project overview
> - **[🛠️ Development Guidelines](docs/DEVELOPMENT_GUIDELINES.md)** - Coding standards and workflows
> - **[🚀 Usage Guide](docs/USAGE_GUIDE.md)** - Step-by-step usage instructions
> - **[⚙️ Environment Setup](docs/ENVIRONMENT_SETUP.md)** - Version verification and setup guide

## 🏗️ 技術棧

### 前端

- **框架**: Vue 3.5+ + TypeScript 5.7+
- **構建工具**: Vite 7.1+
- **狀態管理**: Pinia 2.2+
- **HTTP 客戶端**: Axios 1.7+
- **路由**: Vue Router 4.4+

### 後端

- **框架**: FastAPI + Python 3.13+
- **ORM**: SQLAlchemy (異步)
- **資料庫**: PostgreSQL 16
- **套件管理**: uv 0.4+
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

- **Node.js** 22+ (前端開發)
- **Python** 3.13+ (後端開發)
- **PostgreSQL** 16+ (資料庫)
- **uv** 0.4+ (Python 套件管理)
- **VS Code** (推薦 IDE)
- **Docker** 24+ (可選，容器化開發)

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

## 📚 完整文檔

### 🚀 快速入門文檔
- **[📖 Project Documentation](docs/PROJECT_DOCUMENTATION.md)** - 完整專案文檔，包含架構圖和系統概覽
- **[🚀 Usage Guide](docs/USAGE_GUIDE.md)** - 詳細使用說明，包含所有操作步驟
- **[⚙️ Environment Setup](docs/ENVIRONMENT_SETUP.md)** - 環境設定和版本驗證指南

### 🛠️ 開發文檔
- **[🛠️ Development Guidelines](docs/DEVELOPMENT_GUIDELINES.md)** - 開發守則、編碼規範和工作流程
- **[前端開發指南](frontend/README.md)** - Vue.js 前端開發詳細說明
- **[後端開發指南](backend/README.md)** - FastAPI 後端開發詳細說明
- **[調試指南](DEBUG_GUIDE.md)** - VS Code 調試配置說明

### 📋 技術規範
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

## ⚡ 版本更新說明

本專案已更新至最新穩定版本：

### ✅ 已完成更新
- **Python**: 升級至 3.13+ (工具配置已同步更新)
- **PostgreSQL**: 確認使用 16 版本 ✓
- **Node.js**: 升級至 20+ (建議使用 LTS 版本)
- **Vue.js**: 升級至 3.4+
- **Vite**: 升級至 5.0+
- **TypeScript**: 升級至 5.3+
- **其他前端依賴**: 全面升級至最新穩定版本

### 🔧 配置更新
- `backend/pyproject.toml`: Python 3.13 工具配置已更新
- `frontend/package.json`: 所有依賴包已升級至最新版本
- `docker-compose.yml`: PostgreSQL 16 配置確認正確

詳細的版本驗證和升級指南請參考 **[⚙️ Environment Setup](docs/ENVIRONMENT_SETUP.md)**

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
