# 程式碼風格指南

## 🐍 Python 程式碼風格

### 基本規範

遵循 [PEP 8](https://pep8.org/) 標準，並使用以下工具：

- **Black** - 程式碼格式化
- **isort** - import 排序
- **flake8** - 程式碼檢查
- **mypy** - 類型檢查

### 命名規範

#### 變數和函數

```python
# ✅ 正確：使用 snake_case
user_name = "john_doe"
email_address = "john@example.com"
is_active = True

def get_user_by_id(user_id: int) -> Optional[User]:
    pass

def calculate_total_price(items: List[Item]) -> Decimal:
    pass

# ❌ 錯誤：使用 camelCase
userName = "john_doe"
emailAddress = "john@example.com"

def getUserById(userId: int) -> Optional[User]:
    pass
```

#### 類別

```python
# ✅ 正確：使用 PascalCase
class UserService:
    pass

class DatabaseConnection:
    pass

class EmailValidator:
    pass

# ❌ 錯誤：使用 snake_case
class user_service:
    pass
```

#### 常數

```python
# ✅ 正確：使用 UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30
API_BASE_URL = "https://api.example.com"

# ❌ 錯誤：使用小寫
max_retry_count = 3
```

#### 私有成員

```python
class UserService:
    def __init__(self):
        self._session = None  # 受保護成員
        self.__secret_key = "secret"  # 私有成員

    def _internal_method(self):  # 受保護方法
        pass

    def __private_method(self):  # 私有方法
        pass
```

### 類型提示

```python
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

# ✅ 完整的類型提示
def create_user(
    username: str,
    email: str,
    age: Optional[int] = None,
    tags: List[str] = None
) -> User:
    if tags is None:
        tags = []
    return User(username=username, email=email, age=age, tags=tags)

# ✅ 複雜類型
UserDict = Dict[str, Any]
UserList = List[User]

def process_users(users: UserList) -> Dict[str, UserDict]:
    pass

# ✅ 泛型
from typing import TypeVar, Generic

T = TypeVar('T')

class Repository(Generic[T]):
    def get_by_id(self, id: int) -> Optional[T]:
        pass
```

### 文檔字串

```python
def create_user(username: str, email: str, password: str) -> User:
    """
    創建新用戶

    Args:
        username: 用戶名，長度 3-50 字符
        email: 郵箱地址，必須是有效格式
        password: 密碼，至少 8 字符

    Returns:
        User: 創建的用戶物件

    Raises:
        ValueError: 當用戶名或郵箱已存在時
        ValidationError: 當輸入資料格式錯誤時

    Example:
        >>> user = create_user("john", "john@example.com", "password123")
        >>> print(user.username)
        john
    """
    pass
```

### 錯誤處理

```python
# ✅ 具體的異常處理
try:
    user = await user_service.get_user_by_id(user_id)
except UserNotFoundError:
    logger.warning(f"User {user_id} not found")
    raise HTTPException(status_code=404, detail="User not found")
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")

# ✅ 自定義異常
class UserServiceError(Exception):
    """用戶服務基礎異常"""
    pass

class UserNotFoundError(UserServiceError):
    """用戶不存在異常"""
    pass

class EmailAlreadyExistsError(UserServiceError):
    """郵箱已存在異常"""
    pass

# ❌ 避免捕獲所有異常
try:
    # some code
    pass
except Exception:  # 太寬泛
    pass
```

### 函數設計

```python
# ✅ 單一職責，參數清晰
async def send_welcome_email(user_email: str, username: str) -> bool:
    """發送歡迎郵件"""
    pass

async def validate_user_data(user_data: UserCreate) -> None:
    """驗證用戶資料"""
    pass

# ✅ 使用資料類減少參數數量
from dataclasses import dataclass

@dataclass
class EmailConfig:
    smtp_host: str
    smtp_port: int
    username: str
    password: str
    use_tls: bool = True

async def send_email(config: EmailConfig, to: str, subject: str, body: str) -> bool:
    pass

# ❌ 避免過多參數
async def send_email(
    smtp_host: str,
    smtp_port: int,
    username: str,
    password: str,
    use_tls: bool,
    to: str,
    subject: str,
    body: str
) -> bool:  # 參數太多
    pass
```

### 類別設計

```python
# ✅ 清晰的類別結構
class UserService:
    """用戶服務類，處理用戶相關業務邏輯"""

    def __init__(self, repository: UserRepository):
        self._repository = repository
        self._logger = logging.getLogger(__name__)

    async def create_user(self, user_data: UserCreate) -> User:
        """創建新用戶"""
        # 驗證
        await self._validate_user_data(user_data)

        # 創建
        user = User(**user_data.dict())
        user.hashed_password = self._hash_password(user_data.password)

        # 保存
        return await self._repository.create(user)

    async def _validate_user_data(self, user_data: UserCreate) -> None:
        """驗證用戶資料（私有方法）"""
        if await self._repository.get_by_email(user_data.email):
            raise EmailAlreadyExistsError("Email already exists")

    def _hash_password(self, password: str) -> str:
        """加密密碼（私有方法）"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
```

## 🎯 TypeScript 程式碼風格

### 基本規範

- 使用 **ESLint** 和 **Prettier**
- 啟用嚴格模式：`"strict": true`
- 使用 **camelCase** 命名

### 命名規範

#### 變數和函數

```typescript
// ✅ 正確：使用 camelCase
const userName = "john_doe";
const isLoading = ref(false);
const userList = ref<User[]>([]);

const fetchUserData = async (): Promise<User[]> => {
  // ...
};

const handleFormSubmit = (event: Event): void => {
  // ...
};

// ❌ 錯誤：使用 snake_case
const user_name = "john_doe";
const is_loading = ref(false);

const fetch_user_data = async (): Promise<User[]> => {
  // ...
};
```

#### 類型和介面

```typescript
// ✅ 正確：使用 PascalCase
interface User {
  id: number;
  username: string;
  email: string;
}

type UserStatus = "active" | "inactive" | "pending";

class UserService {
  // ...
}

// ✅ 泛型
interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

// ✅ 聯合類型
type Theme = "light" | "dark" | "auto";
type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";
```

#### 常數

```typescript
// ✅ 正確：使用 UPPER_SNAKE_CASE
const API_BASE_URL = "http://localhost:8000";
const MAX_RETRY_COUNT = 3;
const DEFAULT_PAGE_SIZE = 20;

// ✅ 枚舉
enum UserRole {
  ADMIN = "admin",
  USER = "user",
  MODERATOR = "moderator",
}

// ✅ 常數斷言
const SUPPORTED_LANGUAGES = ["en", "zh", "ja"] as const;
type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];
```

### 類型定義

```typescript
// ✅ 完整的類型定義
interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
}

interface User {
  readonly id: number;
  username: string;
  email: string;
  firstName?: string;
  lastName?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt?: string;
}

// ✅ 工具類型
type PartialUser = Partial<User>;
type UserWithoutId = Omit<User, "id">;
type UserKeys = keyof User;

// ✅ 條件類型
type NonNullable<T> = T extends null | undefined ? never : T;
```

### 函數設計

```typescript
// ✅ 清晰的函數簽名
const createUser = async (userData: CreateUserRequest): Promise<User> => {
  try {
    const response = await apiClient.post<User>("/users", userData);
    return response.data;
  } catch (error) {
    throw new Error(`Failed to create user: ${error.message}`);
  }
};

// ✅ 使用泛型
const fetchData = async <T>(url: string): Promise<T> => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
};

// ✅ 函數重載
function formatDate(date: Date): string;
function formatDate(date: string): string;
function formatDate(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toISOString().split("T")[0];
}
```

### Vue 3 組件風格

```vue
<template>
  <div class="user-card">
    <h3 class="user-card__title">{{ displayName }}</h3>
    <p class="user-card__email">{{ user.email }}</p>
    <div class="user-card__actions">
      <BaseButton variant="primary" @click="handleEdit"> 編輯 </BaseButton>
      <BaseButton variant="danger" @click="handleDelete"> 刪除 </BaseButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { User } from "@/types/user";
import BaseButton from "@/components/ui/BaseButton.vue";

// Props 定義
interface Props {
  user: User;
  showActions?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  showActions: true,
});

// Emits 定義
interface Emits {
  edit: [user: User];
  delete: [userId: number];
}

const emit = defineEmits<Emits>();

// 計算屬性
const displayName = computed(() => {
  const { firstName, lastName, username } = props.user;
  return firstName && lastName ? `${firstName} ${lastName}` : username;
});

// 方法
const handleEdit = (): void => {
  emit("edit", props.user);
};

const handleDelete = (): void => {
  emit("delete", props.user.id);
};
</script>

<style scoped>
.user-card {
  padding: 1rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
}

.user-card__title {
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.user-card__email {
  margin: 0 0 1rem 0;
  color: var(--color-text-secondary);
}

.user-card__actions {
  display: flex;
  gap: 0.5rem;
}
</style>
```

## 🔧 工具配置

### Python 工具配置

#### pyproject.toml

```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["app"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503"]
exclude = [".git", "__pycache__", "build", "dist", ".venv"]
```

#### .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### TypeScript 工具配置

#### .eslintrc.js

```javascript
module.exports = {
  root: true,
  env: {
    node: true,
    browser: true,
    es2022: true,
  },
  extends: [
    "eslint:recommended",
    "@typescript-eslint/recommended",
    "plugin:vue/vue3-recommended",
    "@vue/typescript/recommended",
    "prettier",
  ],
  parser: "vue-eslint-parser",
  parserOptions: {
    parser: "@typescript-eslint/parser",
    ecmaVersion: 2022,
    sourceType: "module",
  },
  rules: {
    // TypeScript
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/explicit-function-return-type": "warn",
    "@typescript-eslint/no-explicit-any": "warn",

    // Vue
    "vue/component-name-in-template-casing": ["error", "PascalCase"],
    "vue/multi-word-component-names": "error",
    "vue/no-unused-vars": "error",

    // General
    "prefer-const": "error",
    "no-var": "error",
    "no-console": process.env.NODE_ENV === "production" ? "warn" : "off",
    "no-debugger": process.env.NODE_ENV === "production" ? "warn" : "off",
  },
};
```

#### .prettierrc

```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 80,
  "useTabs": false,
  "quoteProps": "as-needed",
  "bracketSpacing": true,
  "arrowParens": "avoid",
  "vueIndentScriptAndStyle": true,
  "endOfLine": "lf"
}
```

## 📝 註釋規範

### Python 註釋

```python
# ✅ 好的註釋：解釋為什麼
def calculate_discount(price: Decimal, user_level: str) -> Decimal:
    """
    計算用戶折扣

    VIP 用戶享有額外 10% 折扣，因為他們是我們的重要客戶
    """
    base_discount = price * Decimal('0.1')

    # VIP 用戶額外折扣，提升客戶忠誠度
    if user_level == 'VIP':
        base_discount += price * Decimal('0.1')

    return base_discount

# ❌ 不好的註釋：重複代碼
def calculate_discount(price: Decimal, user_level: str) -> Decimal:
    # 計算基礎折扣
    base_discount = price * 0.1  # 將價格乘以 0.1

    # 如果用戶等級是 VIP
    if user_level == 'VIP':
        # 增加額外折扣
        base_discount += price * 0.1

    # 返回折扣
    return base_discount
```

### TypeScript 註釋

```typescript
// ✅ 好的註釋
/**
 * 用戶認證服務
 *
 * 處理用戶登入、登出和權限驗證
 * 使用 JWT token 進行狀態管理
 */
class AuthService {
  /**
   * 用戶登入
   *
   * @param credentials - 登入憑證
   * @returns Promise<User> - 登入成功的用戶資訊
   * @throws {AuthError} - 當憑證無效時拋出
   */
  async login(credentials: LoginCredentials): Promise<User> {
    // 使用 bcrypt 比較密碼，確保安全性
    const isValid = await bcrypt.compare(
      credentials.password,
      user.hashedPassword,
    );

    if (!isValid) {
      throw new AuthError("Invalid credentials");
    }

    return user;
  }
}

// ❌ 不好的註釋
class AuthService {
  // 登入函數
  async login(credentials: LoginCredentials): Promise<User> {
    // 比較密碼
    const isValid = await bcrypt.compare(
      credentials.password,
      user.hashedPassword,
    );

    // 如果無效
    if (!isValid) {
      // 拋出錯誤
      throw new AuthError("Invalid credentials");
    }

    // 返回用戶
    return user;
  }
}
```

## ✅ 程式碼審查清單

### Python 審查要點

- [ ] 遵循 PEP 8 規範
- [ ] 所有函數都有類型提示
- [ ] 所有公開函數都有文檔字串
- [ ] 異常處理具體且適當
- [ ] 沒有硬編碼的魔術數字
- [ ] 變數命名清晰有意義
- [ ] 函數職責單一
- [ ] 沒有重複代碼

### TypeScript 審查要點

- [ ] 所有變數都有明確類型
- [ ] 沒有使用 `any` 類型
- [ ] 組件 props 和 emits 都有類型定義
- [ ] 函數有明確的返回類型
- [ ] 使用適當的 Vue 3 Composition API
- [ ] CSS 類名遵循 BEM 規範
- [ ] 沒有未使用的導入

### 通用審查要點

- [ ] 程式碼格式一致
- [ ] 註釋有意義且必要
- [ ] 沒有調試代碼（console.log 等）
- [ ] 錯誤處理完善
- [ ] 性能考量適當
- [ ] 安全性考量充分
