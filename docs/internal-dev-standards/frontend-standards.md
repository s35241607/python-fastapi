# 前端工程師開發規範 Frontend Development Standards

## 目錄 Table of Contents

1. [技術棧規範](#技術棧規範)
2. [專案結構](#專案結構)
3. [程式碼規範](#程式碼規範)
4. [元件開發規範](#元件開發規範)
5. [狀態管理規範](#狀態管理規範)
6. [API 整合規範](#api-整合規範)
7. [測試規範](#測試規範)
8. [效能優化規範](#效能優化規範)
9. [UI/UX 規範](#uiux-規範)
10. [環境配置](#環境配置)

## 技術棧規範

### 核心技術
- **建構工具**: Vite (最新穩定版)
- **框架**: Vue 3.5+ (Composition API)
- **類型系統**: TypeScript 5.9+
- **狀態管理**: Pinia
- **HTTP 客戶端**: Axios
- **UI 框架**: Vuetify 3+
- **路由**: Vue Router 4+

### 程式碼品質工具
```json
{
  "prettier": "^3.0.0",
  "eslint": "^8.0.0",
  "@typescript-eslint/eslint-plugin": "^6.0.0",
  "@typescript-eslint/parser": "^6.0.0",
  "eslint-plugin-vue": "^9.0.0"
}
```

## 專案結構

```
src/
├── components/          # 可重用元件
│   ├── common/         # 通用元件
│   ├── layout/         # 布局元件
│   └── business/       # 業務元件
├── views/              # 頁面元件
├── stores/             # Pinia 狀態管理
├── services/           # API 服務
├── composables/        # 組合式函數
├── types/              # TypeScript 類型定義
├── utils/              # 工具函數
├── assets/             # 靜態資源
├── router/             # 路由配置
├── plugins/            # 插件配置
└── styles/             # 全域樣式
```

## 程式碼規範

### 命名規則

#### 檔案命名
```typescript
// 元件檔案 - PascalCase
UserProfile.vue
NavigationMenu.vue

// 非元件檔案 - camelCase
userService.ts
apiClient.ts

// 類型定義檔案 - camelCase with .types.ts
userProfile.types.ts
apiResponse.types.ts
```

#### 變數與函數命名
```typescript
// 變數 - camelCase
const userName = 'john'
const isUserActive = true

// 函數 - camelCase，動詞開頭
function getUserData() {}
function handleSubmit() {}

// 常數 - UPPER_SNAKE_CASE
const API_BASE_URL = 'https://api.example.com'
const MAX_RETRY_COUNT = 3

// 類型 - PascalCase
interface UserProfile {
  id: number
  name: string
}

type ApiResponse<T> = {
  data: T
  success: boolean
}
```

### ESLint + Prettier 配置

#### .eslintrc.cjs
```javascript
module.exports = {
  env: {
    node: true,
    browser: true,
    es2022: true
  },
  extends: [
    'eslint:recommended',
    '@vue/eslint-config-typescript',
    '@vue/eslint-config-prettier'
  ],
  parserOptions: {
    ecmaVersion: 'latest'
  },
  rules: {
    'vue/multi-word-component-names': 'off',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'prefer-const': 'error',
    'no-var': 'error'
  }
}
```

#### .prettierrc
```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "none",
  "printWidth": 80,
  "endOfLine": "lf"
}
```

### TypeScript 規範

#### 類型定義
```typescript
// 介面定義 - 使用 interface
interface User {
  readonly id: number
  name: string
  email: string
  roles: Role[]
  createdAt: Date
  updatedAt?: Date
}

// 聯合類型 - 使用 type
type UserStatus = 'active' | 'inactive' | 'pending'
type ApiMethod = 'GET' | 'POST' | 'PUT' | 'DELETE'

// 泛型定義
interface ApiResponse<T> {
  data: T
  message: string
  success: boolean
  timestamp: number
}
```

#### 空值處理
```typescript
// 使用可選鏈
const userName = user?.profile?.name ?? 'Unknown'

// 明確的 null 檢查
if (data !== null && data !== undefined) {
  // 處理邏輯
}

// 使用類型守衛
function isValidUser(user: unknown): user is User {
  return user !== null && typeof user === 'object' && 'id' in user
}
```

## 元件開發規範

### 元件結構
```vue
<template>
  <!-- 模板內容 -->
</template>

<script setup lang="ts">
// 導入順序：
// 1. Vue 相關
// 2. 第三方庫
// 3. 專案內部模組
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

// Props 定義
interface Props {
  userId: number
  showActions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showActions: true
})

// Emits 定義
interface Emits {
  update: [user: User]
  delete: [id: number]
}

const emit = defineEmits<Emits>()

// 響應式數據
const isLoading = ref(false)
const userData = ref<User | null>(null)

// 計算屬性
const displayName = computed(() => {
  return userData.value?.name ?? 'Unknown User'
})

// 方法
const handleUpdate = async () => {
  try {
    isLoading.value = true
    // 更新邏輯
    emit('update', userData.value!)
  } catch (error) {
    console.error('Update failed:', error)
  } finally {
    isLoading.value = false
  }
}

// 生命週期
onMounted(async () => {
  await loadUserData()
})
</script>

<style scoped>
/* 元件樣式 */
</style>
```

### 元件設計原則

1. **單一職責**: 每個元件只負責一個功能
2. **可重用性**: 設計時考慮可重用性
3. **Props 驗證**: 明確定義 Props 類型
4. **事件命名**: 使用動詞-名詞格式 (update:user, delete:item)
5. **插槽使用**: 提供適當的插槽擴展點

### 元件測試
```typescript
// UserProfile.test.ts
import { mount } from '@vue/test-utils'
import UserProfile from './UserProfile.vue'

describe('UserProfile', () => {
  it('renders user name correctly', () => {
    const wrapper = mount(UserProfile, {
      props: {
        user: {
          id: 1,
          name: 'John Doe',
          email: 'john@example.com'
        }
      }
    })

    expect(wrapper.text()).toContain('John Doe')
  })
})
```

## 狀態管理規範

### Pinia Store 結構
```typescript
// stores/user.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, UserProfile } from '@/types/user.types'
import { userService } from '@/services/userService'

export const useUserStore = defineStore('user', () => {
  // State
  const currentUser = ref<User | null>(null)
  const users = ref<User[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => currentUser.value !== null)
  const userCount = computed(() => users.value.length)

  // Actions
  const login = async (credentials: LoginCredentials) => {
    try {
      isLoading.value = true
      error.value = null

      const user = await userService.login(credentials)
      currentUser.value = user

      return user
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Login failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const logout = () => {
    currentUser.value = null
    error.value = null
  }

  const fetchUsers = async () => {
    try {
      isLoading.value = true
      users.value = await userService.getUsers()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch users'
    } finally {
      isLoading.value = false
    }
  }

  return {
    // State
    currentUser,
    users,
    isLoading,
    error,
    // Getters
    isAuthenticated,
    userCount,
    // Actions
    login,
    logout,
    fetchUsers
  }
})
```

### Store 使用規範

1. **命名規範**: use{EntityName}Store
2. **狀態分類**: 明確區分 state、getters、actions
3. **錯誤處理**: 統一的錯誤處理模式
4. **Loading 狀態**: 提供 loading 狀態管理
5. **類型安全**: 完整的 TypeScript 類型定義

## API 整合規範

### API 服務結構
```typescript
// services/apiClient.ts
import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'

class ApiClient {
  private instance: AxiosInstance

  constructor() {
    this.instance = axios.create({
      baseURL: import.meta.env.VITE_API_GATEWAY_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // 請求攔截器
    this.instance.interceptors.request.use(
      (config) => {
        const authStore = useAuthStore()
        const token = authStore.getToken()

        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        return config
      },
      (error) => Promise.reject(error)
    )

    // 響應攔截器
    this.instance.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          const authStore = useAuthStore()
          await authStore.logout()
        }
        return Promise.reject(error)
      }
    )
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.get<T>(url, config)
    return response.data
  }

  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.post<T>(url, data, config)
    return response.data
  }

  // PUT, DELETE 方法...
}

export const apiClient = new ApiClient()
```

### 服務層實作
```typescript
// services/userService.ts
import { apiClient } from './apiClient'
import type { User, CreateUserRequest, UpdateUserRequest } from '@/types/user.types'

export const userService = {
  async getUsers(): Promise<User[]> {
    return apiClient.get<User[]>('/api/users')
  },

  async getUserById(id: number): Promise<User> {
    return apiClient.get<User>(`/api/users/${id}`)
  },

  async createUser(data: CreateUserRequest): Promise<User> {
    return apiClient.post<User>('/api/users', data)
  },

  async updateUser(id: number, data: UpdateUserRequest): Promise<User> {
    return apiClient.put<User>(`/api/users/${id}`, data)
  },

  async deleteUser(id: number): Promise<void> {
    return apiClient.delete(`/api/users/${id}`)
  }
}
```

## 測試規範

### 單元測試結構
```typescript
// tests/components/UserProfile.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import UserProfile from '@/components/UserProfile.vue'
import { useUserStore } from '@/stores/user'

describe('UserProfile Component', () => {
  let wrapper: VueWrapper
  let userStore: ReturnType<typeof useUserStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    userStore = useUserStore()

    wrapper = mount(UserProfile, {
      props: {
        userId: 1
      },
      global: {
        plugins: [createPinia()]
      }
    })
  })

  it('displays user information correctly', async () => {
    const mockUser = {
      id: 1,
      name: 'John Doe',
      email: 'john@example.com'
    }

    userStore.currentUser = mockUser
    await wrapper.vm.$nextTick()

    expect(wrapper.find('[data-testid="user-name"]').text()).toBe('John Doe')
    expect(wrapper.find('[data-testid="user-email"]').text()).toBe('john@example.com')
  })

  it('handles loading state', async () => {
    userStore.isLoading = true
    await wrapper.vm.$nextTick()

    expect(wrapper.find('[data-testid="loading"]').exists()).toBe(true)
  })
})
```

### E2E 測試
```typescript
// tests/e2e/user-management.spec.ts
import { test, expect } from '@playwright/test'

test.describe('User Management', () => {
  test('should create new user', async ({ page }) => {
    await page.goto('/users')

    await page.click('[data-testid="add-user-btn"]')
    await page.fill('[data-testid="user-name-input"]', 'Test User')
    await page.fill('[data-testid="user-email-input"]', 'test@example.com')
    await page.click('[data-testid="submit-btn"]')

    await expect(page.locator('[data-testid="success-message"]')).toBeVisible()
  })
})
```

## 效能優化規範

### 代碼分割
```typescript
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/users',
    name: 'Users',
    component: () => import('@/views/Users.vue') // 動態導入
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue')
  }
]
```

### 圖片優化
```vue
<template>
  <!-- 使用 Vite 的圖片優化 -->
  <img
    :src="imageUrl"
    :alt="imageAlt"
    loading="lazy"
    decoding="async"
  />
</template>

<script setup lang="ts">
// 導入優化後的圖片
import heroImage from '@/assets/images/hero.jpg?w=800&format=webp'
</script>
```

### 虛擬滾動
```vue
<template>
  <VVirtualScroll
    :items="largeDataSet"
    :item-height="50"
    height="400px"
  >
    <template #default="{ item }">
      <UserItem :user="item" />
    </template>
  </VVirtualScroll>
</template>
```

## UI/UX 規範

### Vuetify 主題配置
```typescript
// plugins/vuetify.ts
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const customTheme = {
  dark: false,
  colors: {
    primary: '#1976D2',
    secondary: '#424242',
    accent: '#82B1FF',
    error: '#FF5252',
    info: '#2196F3',
    success: '#4CAF50',
    warning: '#FFC107'
  }
}

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'customTheme',
    themes: {
      customTheme
    }
  }
})
```

### 響應式設計
```vue
<template>
  <VContainer fluid>
    <VRow>
      <VCol
        cols="12"
        sm="6"
        md="4"
        lg="3"
      >
        <UserCard :user="user" />
      </VCol>
    </VRow>
  </VContainer>
</template>
```

### 無障礙設計
```vue
<template>
  <VBtn
    :aria-label="buttonLabel"
    :aria-describedby="helpTextId"
    @click="handleAction"
  >
    {{ buttonText }}
  </VBtn>

  <div :id="helpTextId" class="sr-only">
    {{ helpText }}
  </div>
</template>
```

## 環境配置

### 環境變數
```typescript
// env.d.ts
interface ImportMetaEnv {
  readonly VITE_AUTH_COOKIE_NAME: string
  readonly VITE_SSO_LOGIN_URL: string
  readonly VITE_API_GATEWAY_URL: string
  readonly VITE_APP_TITLE: string
  readonly VITE_APP_VERSION: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
```

### Vite 配置
```typescript
// vite.config.ts
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'
import path from 'path'

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [
      vue(),
      vuetify({ autoImport: true })
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src')
      }
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: env.VITE_API_GATEWAY_URL,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    },
    build: {
      target: 'esnext',
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['vue', 'vue-router', 'pinia'],
            ui: ['vuetify']
          }
        }
      }
    }
  }
})
```

## CI/CD 整合

### package.json 腳本
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc --noEmit && vite build",
    "preview": "vite preview",
    "type-check": "vue-tsc --noEmit",
    "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts --fix",
    "lint:check": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "test:unit": "vitest",
    "test:e2e": "playwright test",
    "test:coverage": "vitest --coverage"
  }
}
```

### GitLab CI 配置
```yaml
# .gitlab-ci.yml (frontend部分)
frontend:lint:
  stage: test
  script:
    - cd frontend
    - npm ci
    - npm run lint:check
    - npm run format:check
  only:
    - merge_requests
    - main

frontend:test:
  stage: test
  script:
    - cd frontend
    - npm ci
    - npm run test:unit
    - npm run test:coverage
  coverage: '/Lines\s*:\s*(\d+\.?\d*)%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: frontend/coverage/cobertura-coverage.xml

frontend:build:
  stage: build
  script:
    - cd frontend
    - npm ci
    - npm run build
  artifacts:
    paths:
      - frontend/dist/
    expire_in: 1 day
```

## 最佳實踐檢查清單

### 開發前檢查
- [ ] 確認需求理解正確
- [ ] 設計 API 介面
- [ ] 設計元件結構
- [ ] 設置開發環境

### 開發中檢查
- [ ] 遵循命名規範
- [ ] 添加適當的類型定義
- [ ] 實作錯誤處理
- [ ] 添加 loading 狀態
- [ ] 考慮無障礙設計

### 開發後檢查
- [ ] 程式碼通過 lint 檢查
- [ ] 單元測試覆蓋率達標
- [ ] E2E 測試通過
- [ ] 效能符合要求
- [ ] 文檔更新完成

---

*最後更新: 2025-01-XX*
