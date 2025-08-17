# 前端開發規範

## 🏗️ 專案架構

### 目錄結構

```
frontend/
├── src/
│   ├── components/        # 可重用組件
│   │   ├── common/        # 通用組件
│   │   ├── forms/         # 表單組件
│   │   └── ui/            # UI 組件
│   ├── views/             # 頁面組件
│   │   ├── auth/          # 認證相關頁面
│   │   ├── user/          # 用戶相關頁面
│   │   └── dashboard/     # 儀表板頁面
│   ├── composables/       # 組合式函數
│   │   ├── useAuth.ts     # 認證邏輯
│   │   ├── useApi.ts      # API 調用
│   │   └── useUtils.ts    # 工具函數
│   ├── stores/            # Pinia 狀態管理
│   │   ├── auth.ts        # 認證狀態
│   │   ├── user.ts        # 用戶狀態
│   │   └── app.ts         # 應用狀態
│   ├── services/          # API 服務層
│   │   ├── api.ts         # API 基礎配置
│   │   ├── auth.service.ts
│   │   └── user.service.ts
│   ├── types/             # TypeScript 類型定義
│   │   ├── api.ts         # API 相關類型
│   │   ├── user.ts        # 用戶相關類型
│   │   └── common.ts      # 通用類型
│   ├── utils/             # 工具函數
│   │   ├── validators.ts  # 驗證函數
│   │   ├── formatters.ts  # 格式化函數
│   │   └── constants.ts   # 常數定義
│   ├── assets/            # 靜態資源
│   │   ├── images/
│   │   ├── icons/
│   │   └── styles/
│   ├── router/            # 路由配置
│   └── main.ts
```

## 📝 命名規則

### 檔案命名

- 組件檔案：PascalCase - `UserProfile.vue`
- 工具檔案：camelCase - `apiClient.ts`
- 頁面檔案：PascalCase - `UserDashboard.vue`
- 類型檔案：camelCase - `userTypes.ts`

### 組件命名

```vue
<!-- ✅ 正確：使用 PascalCase -->
<template>
  <UserProfileCard :user="currentUser" />
  <BaseButton @click="handleClick">提交</BaseButton>
</template>

<!-- ❌ 錯誤：使用 kebab-case -->
<template>
  <user-profile-card :user="currentUser" />
  <base-button @click="handleClick">提交</base-button>
</template>
```

### 變數和函數命名

```typescript
// ✅ 正確：使用 camelCase
const userName = ref("");
const isLoading = ref(false);

const fetchUserData = async () => {
  // ...
};

const handleFormSubmit = () => {
  // ...
};

// ✅ 常數使用 UPPER_SNAKE_CASE
const API_BASE_URL = "http://localhost:8000";
const MAX_RETRY_COUNT = 3;
```

## 🎯 Vue 3 Composition API 規範

### 1. 組件結構

```vue
<template>
  <!-- 模板內容 -->
</template>

<script setup lang="ts">
// 1. 導入
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import type { User } from "@/types/user";

// 2. Props 定義
interface Props {
  userId: number;
  showActions?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  showActions: true,
});

// 3. Emits 定義
interface Emits {
  update: [user: User];
  delete: [userId: number];
}

const emit = defineEmits<Emits>();

// 4. 響應式數據
const user = ref<User | null>(null);
const isLoading = ref(false);
const error = ref<string | null>(null);

// 5. 計算屬性
const displayName = computed(() => {
  return user.value ? `${user.value.firstName} ${user.value.lastName}` : "";
});

// 6. 方法
const fetchUser = async () => {
  try {
    isLoading.value = true;
    error.value = null;
    // API 調用
  } catch (err) {
    error.value = "獲取用戶資料失敗";
  } finally {
    isLoading.value = false;
  }
};

// 7. 生命週期
onMounted(() => {
  fetchUser();
});

// 8. 暴露給模板的方法（如果需要）
defineExpose({
  fetchUser,
});
</script>

<style scoped>
/* 樣式 */
</style>
```

### 2. Composables 規範

```typescript
// composables/useAuth.ts
import { ref, computed } from "vue";
import type { User } from "@/types/user";

export function useAuth() {
  const user = ref<User | null>(null);
  const isAuthenticated = computed(() => !!user.value);
  const isLoading = ref(false);

  const login = async (credentials: LoginCredentials) => {
    try {
      isLoading.value = true;
      // 登入邏輯
    } catch (error) {
      throw new Error("登入失敗");
    } finally {
      isLoading.value = false;
    }
  };

  const logout = () => {
    user.value = null;
    // 清除 token 等
  };

  return {
    // 狀態
    user: readonly(user),
    isAuthenticated,
    isLoading: readonly(isLoading),

    // 方法
    login,
    logout,
  };
}
```

## 🗃️ 狀態管理 (Pinia)

### Store 結構

```typescript
// stores/user.ts
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { User } from "@/types/user";
import { userService } from "@/services/user.service";

export const useUserStore = defineStore("user", () => {
  // State
  const users = ref<User[]>([]);
  const currentUser = ref<User | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Getters
  const activeUsers = computed(() =>
    users.value.filter((user) => user.isActive),
  );

  const userCount = computed(() => users.value.length);

  // Actions
  const fetchUsers = async () => {
    try {
      isLoading.value = true;
      error.value = null;
      users.value = await userService.getUsers();
    } catch (err) {
      error.value = "獲取用戶列表失敗";
      console.error("Failed to fetch users:", err);
    } finally {
      isLoading.value = false;
    }
  };

  const createUser = async (userData: CreateUserRequest) => {
    try {
      const newUser = await userService.createUser(userData);
      users.value.push(newUser);
      return newUser;
    } catch (err) {
      error.value = "創建用戶失敗";
      throw err;
    }
  };

  const updateUser = async (userId: number, userData: UpdateUserRequest) => {
    try {
      const updatedUser = await userService.updateUser(userId, userData);
      const index = users.value.findIndex((user) => user.id === userId);
      if (index !== -1) {
        users.value[index] = updatedUser;
      }
      return updatedUser;
    } catch (err) {
      error.value = "更新用戶失敗";
      throw err;
    }
  };

  const deleteUser = async (userId: number) => {
    try {
      await userService.deleteUser(userId);
      users.value = users.value.filter((user) => user.id !== userId);
    } catch (err) {
      error.value = "刪除用戶失敗";
      throw err;
    }
  };

  const clearError = () => {
    error.value = null;
  };

  return {
    // State
    users,
    currentUser,
    isLoading,
    error,

    // Getters
    activeUsers,
    userCount,

    // Actions
    fetchUsers,
    createUser,
    updateUser,
    deleteUser,
    clearError,
  };
});
```

## 🌐 API 服務層

### 基礎 API 配置

```typescript
// services/api.ts
import axios, { type AxiosInstance, type AxiosRequestConfig } from "axios";

class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        "Content-Type": "application/json",
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // 請求攔截器
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem("access_token");
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error),
    );

    // 響應攔截器
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // 處理未授權
          localStorage.removeItem("access_token");
          window.location.href = "/login";
        }
        return Promise.reject(error);
      },
    );
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig,
  ): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig,
  ): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }
}

export const apiClient = new ApiClient(import.meta.env.VITE_API_URL);
```

### 具體服務

```typescript
// services/user.service.ts
import { apiClient } from "./api";
import type { User, CreateUserRequest, UpdateUserRequest } from "@/types/user";

export const userService = {
  async getUsers(): Promise<User[]> {
    return apiClient.get<User[]>("/users");
  },

  async getUserById(id: number): Promise<User> {
    return apiClient.get<User>(`/users/${id}`);
  },

  async createUser(userData: CreateUserRequest): Promise<User> {
    return apiClient.post<User>("/users", userData);
  },

  async updateUser(id: number, userData: UpdateUserRequest): Promise<User> {
    return apiClient.put<User>(`/users/${id}`, userData);
  },

  async deleteUser(id: number): Promise<void> {
    return apiClient.delete<void>(`/users/${id}`);
  },
};
```

## 📝 TypeScript 類型定義

```typescript
// types/user.ts
export interface User {
  id: number;
  email: string;
  username: string;
  firstName?: string;
  lastName?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt?: string;
}

export interface CreateUserRequest {
  email: string;
  username: string;
  password: string;
  firstName?: string;
  lastName?: string;
}

export interface UpdateUserRequest {
  email?: string;
  username?: string;
  firstName?: string;
  lastName?: string;
  isActive?: boolean;
}

// types/api.ts
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}
```

## 🎨 樣式規範

### CSS 模組化

```vue
<template>
  <div :class="$style.container">
    <h1 :class="$style.title">標題</h1>
    <button :class="[$style.button, $style.primary]">按鈕</button>
  </div>
</template>

<style module>
.container {
  padding: 1rem;
}

.title {
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 1rem;
}

.button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;

  &.primary {
    background-color: #3b82f6;
    color: white;

    &:hover {
      background-color: #2563eb;
    }
  }
}
</style>
```

### CSS 變數使用

```css
/* assets/styles/variables.css */
:root {
  /* 顏色 */
  --color-primary: #3b82f6;
  --color-secondary: #6b7280;
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;

  /* 間距 */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;

  /* 字體 */
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
}
```

## 🧪 測試規範

### 組件測試

```typescript
// tests/components/UserCard.test.ts
import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import UserCard from "@/components/UserCard.vue";
import type { User } from "@/types/user";

const mockUser: User = {
  id: 1,
  email: "test@example.com",
  username: "testuser",
  firstName: "Test",
  lastName: "User",
  isActive: true,
  createdAt: "2023-01-01T00:00:00Z",
};

describe("UserCard", () => {
  it("renders user information correctly", () => {
    const wrapper = mount(UserCard, {
      props: { user: mockUser },
    });

    expect(wrapper.text()).toContain("Test User");
    expect(wrapper.text()).toContain("test@example.com");
  });

  it("emits delete event when delete button is clicked", async () => {
    const wrapper = mount(UserCard, {
      props: { user: mockUser, showActions: true },
    });

    await wrapper.find('[data-testid="delete-button"]').trigger("click");

    expect(wrapper.emitted("delete")).toBeTruthy();
    expect(wrapper.emitted("delete")?.[0]).toEqual([mockUser.id]);
  });
});
```

## 🔧 工具配置

### ESLint 配置

```javascript
// .eslintrc.js
module.exports = {
  extends: ["@vue/typescript/recommended", "plugin:vue/vue3-recommended"],
  rules: {
    "vue/component-name-in-template-casing": ["error", "PascalCase"],
    "vue/multi-word-component-names": "error",
    "@typescript-eslint/no-unused-vars": "error",
    "prefer-const": "error",
  },
};
```

### Prettier 配置

```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 80,
  "vueIndentScriptAndStyle": true
}
```

## ✅ 最佳實踐

### 1. 性能優化

- 使用 `v-memo` 優化列表渲染
- 合理使用 `shallowRef` 和 `shallowReactive`
- 組件懶加載

### 2. 可訪問性

- 使用語義化 HTML
- 添加適當的 ARIA 屬性
- 確保鍵盤導航

### 3. 錯誤處理

- 使用 `ErrorBoundary` 組件
- 全局錯誤處理
- 用戶友好的錯誤訊息

### 4. 代碼組織

- 單一職責原則
- 可重用組件設計
- 適當的抽象層級
