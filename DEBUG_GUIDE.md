# VS Code Debug 指南

## 🚀 快速開始

### 1. 啟動 Debug 模式

- 按 **F5** 或點擊 VS Code 左側的 Debug 圖標
- 選擇 **"Python: FastAPI Debug"** 配置
- 後端將在 debug 模式下啟動在 http://127.0.0.1:8000

### 2. 設置斷點

在以下位置設置斷點來測試 debug 功能：

#### 後端斷點位置：

- `backend/app/routers/users.py` 第 12 行：檢查輸入資料
- `backend/app/routers/users.py` 第 19 行：密碼處理
- `backend/app/routers/users.py` 第 35 行：資料庫操作
- `backend/app/main.py` 第 35 行：根路徑處理

### 3. 測試 Debug

1. 啟動 debug 後，訪問：http://127.0.0.1:8000
2. 訪問 API 文檔：http://127.0.0.1:8000/docs
3. 測試用戶 API：
   - GET http://127.0.0.1:8000/api/v1/users/
   - POST http://127.0.0.1:8000/api/v1/users/

## 🔧 Debug 配置說明

### 可用的 Debug 配置：

1. **Python: FastAPI Debug** - 後端 debug
2. **Vue.js: Debug** - 前端 debug
3. **Launch Full Stack** - 同時啟動前後端

### Debug 功能：

- ✅ 斷點調試
- ✅ 變數檢查
- ✅ 調用堆疊
- ✅ 熱重載
- ✅ 控制台輸出

## 🎯 Debug 技巧

### 1. 檢查變數

- 在 debug 暫停時，將滑鼠懸停在變數上查看值
- 使用 "Variables" 面板查看所有局部變數
- 使用 "Watch" 面板監控特定表達式

### 2. 控制台調試

- 在 debug 暫停時，使用 "Debug Console" 執行 Python 代碼
- 例如：`print(user.email)` 或 `len(users)`

### 3. 條件斷點

- 右鍵點擊斷點，選擇 "Edit Breakpoint"
- 設置條件，例如：`user.email == "test@example.com"`

## 🌐 前端 Debug

### 啟動前端 Debug：

```bash
cd frontend
npm run dev
```

### 瀏覽器 Debug：

- 在瀏覽器中按 F12 打開開發者工具
- 在 Sources 標籤中設置 JavaScript 斷點
- 使用 Vue DevTools 擴展調試 Vue 組件

## 🔍 常見問題

### 1. 斷點不生效

- 確保選擇了正確的 debug 配置
- 檢查 Python 解釋器路徑是否正確
- 重新啟動 debug 會話

### 2. 資料庫連接失敗

- 確保 PostgreSQL 容器正在運行：`docker ps`
- 檢查 .env 文件中的資料庫 URL

### 3. 前端無法連接後端

- 確保後端在 127.0.0.1:8000 運行
- 檢查 CORS 設置
- 查看瀏覽器控制台錯誤

## 📝 Debug 日誌

Debug 模式下會顯示詳細日誌：

- 🔍 表示 debug 信息
- ✅ 表示成功操作
- ❌ 表示錯誤
- 🚀 表示啟動信息
