# Vue.js 前端應用

基於 Vue 3 + TypeScript + Vite 構建的現代化前端應用。

## 🛠️ 技術棧

- **Vue 3** - 漸進式 JavaScript 框架
- **TypeScript** - 類型安全的 JavaScript
- **Vite** - 快速的前端構建工具
- **Vue Router** - 官方路由管理器
- **Pinia** - Vue 3 狀態管理
- **Axios** - HTTP 客戶端
- **ESLint + Prettier** - 程式碼檢查和格式化

## 🚀 快速開始

### 環境需求

- Node.js 18+
- npm 或 yarn

### 安裝依賴

```bash
# 使用 npm
npm install

# 或使用 yarn
yarn install
```

### 開發模式

```bash
# 啟動開發伺服器
npm run dev

# 開發伺服器會在 http://localhost:5173 啟動
```

### 建置專案

```bash
# 建置生產版本
npm run build

# 預覽建置結果
npm run preview
```

## 📁 專案結構

```
frontend/
├── public/                 # 靜態資源
├── src/
│   ├── components/         # Vue 組件
│   ├── views/             # 頁面組件
│   ├── router/            # 路由配置
│   ├── stores/            # Pinia 狀態管理
│   ├── services/          # API 服務
│   ├── types/             # TypeScript 類型定義
│   ├── utils/             # 工具函數
│   ├── assets/            # 資源文件
│   ├── App.vue            # 根組件
│   └── main.ts            # 應用入口
├── index.html             # HTML 模板
├── vite.config.ts         # Vite 配置
├── tsconfig.json          # TypeScript 配置
├── package.json           # 專案配置
└── README.md              # 本文件
```

## 🔧 開發指南

### 程式碼規範

專案使用 ESLint 和 Prettier 來維護程式碼品質：

```bash
# 檢查程式碼
npm run lint

# 自動修復程式碼問題
npm run lint --fix

# 格式化程式碼
npm run format
```

### 組件開發

#### 創建新組件

```vue
<template>
  <div class="my-component">
    <h2>{{ title }}</h2>
    <p>{{ description }}</p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title: string;
  description?: string;
}

defineProps<Props>();
</script>

<style scoped>
.my-component {
  padding: 1rem;
}
</style>
```

#### 組件命名規範

- 使用 PascalCase 命名組件文件
- 組件名稱應該具有描述性
- 避免使用 HTML 標籤名稱

### 狀態管理 (Pinia)

```typescript
// stores/user.ts
import { defineStore } from "pinia";

export const useUserStore = defineStore("user", {
  state: () => ({
    user: null as User | null,
    isLoggedIn: false,
  }),

  getters: {
    userName: (state) => state.user?.name || "Guest",
  },

  actions: {
    async login(credentials: LoginCredentials) {
      // 登入邏輯
    },

    logout() {
      this.user = null;
      this.isLoggedIn = false;
    },
  },
});
```

### API 服務

```typescript
// services/api.ts
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: 10000,
});

// 請求攔截器
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 響應攔截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 處理未授權錯誤
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

export default api;
```

### 路由配置

```typescript
// router/index.ts
import { createRouter, createWebHistory } from "vue-router";
import Home from "@/views/Home.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "Home",
      component: Home,
    },
    {
      path: "/about",
      name: "About",
      component: () => import("@/views/About.vue"), // 懶加載
    },
  ],
});

export default router;
```

## 🌍 環境變數

創建 `.env` 檔案來配置環境變數：

```bash
# API 基礎 URL
VITE_API_BASE_URL=http://localhost:8000

# 應用標題
VITE_APP_TITLE=Vue Frontend

# 其他配置...
```

### 環境變數使用

```typescript
// 在 TypeScript 中使用
const apiUrl = import.meta.env.VITE_API_BASE_URL;
const appTitle = import.meta.env.VITE_APP_TITLE;
```

## 🧪 測試

### 單元測試 (待配置)

```bash
# 安裝測試依賴
npm install -D vitest @vue/test-utils jsdom

# 執行測試
npm run test

# 測試覆蓋率
npm run test:coverage
```

### E2E 測試 (待配置)

```bash
# 安裝 Cypress
npm install -D cypress

# 執行 E2E 測試
npm run test:e2e
```

## 📦 建置和部署

### 建置配置

```typescript
// vite.config.ts
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["vue", "vue-router", "pinia"],
          utils: ["axios"],
        },
      },
    },
  },
});
```

### 部署

#### 靜態部署 (Netlify, Vercel)

```bash
# 建置專案
npm run build

# dist/ 目錄包含所有靜態文件
```

#### Docker 部署

```dockerfile
# Dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Nginx 配置

```nginx
# nginx.conf
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # SPA 路由支援
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理 (可選)
    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔍 除錯和開發工具

### VS Code 配置

推薦安裝的擴充套件：

- Vue Language Features (Volar)
- TypeScript Vue Plugin (Volar)
- ESLint
- Prettier
- Auto Rename Tag

### 瀏覽器開發工具

- **Vue DevTools** - Vue 3 專用開發工具
- **Pinia DevTools** - 狀態管理除錯

### 效能監控

```typescript
// 效能監控範例
import { onMounted } from "vue";

onMounted(() => {
  // 監控首屏載入時間
  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      console.log("Performance:", entry);
    }
  });

  observer.observe({ entryTypes: ["navigation", "paint"] });
});
```

## 🚨 常見問題

### Q: 開發伺服器啟動失敗

**A**: 檢查 Node.js 版本是否為 18+，刪除 `node_modules` 重新安裝依賴

### Q: 無法連接後端 API

**A**: 確認後端服務正在運行，檢查 `VITE_API_BASE_URL` 環境變數

### Q: 建置後路由不工作

**A**: 確保伺服器配置支援 SPA 路由，參考上方 Nginx 配置

### Q: TypeScript 類型錯誤

**A**: 檢查 `tsconfig.json` 配置，確保類型定義文件正確

## 📚 學習資源

- [Vue 3 官方文檔](https://vuejs.org/)
- [Vite 官方文檔](https://vitejs.dev/)
- [Pinia 官方文檔](https://pinia.vuejs.org/)
- [Vue Router 官方文檔](https://router.vuejs.org/)
- [TypeScript 官方文檔](https://www.typescriptlang.org/)

## 🤝 貢獻指南

1. 遵循現有的程式碼風格
2. 為新功能添加適當的測試
3. 更新相關文檔
4. 提交前執行 `npm run lint` 檢查程式碼
