# API 設計規範 API Design Standards

## 目錄 Table of Contents

1. [RESTful 設計原則](#restful-設計原則)
2. [URL 設計規範](#url-設計規範)
3. [HTTP 方法使用](#http-方法使用)
4. [請求/回應格式](#請求回應格式)
5. [狀態碼規範](#狀態碼規範)
6. [錯誤處理](#錯誤處理)
7. [版本控管](#版本控管)
8. [認證與授權](#認證與授權)
9. [API 文檔](#api-文檔)

## RESTful 設計原則

### 核心原則
1. **資源導向**: API 圍繞資源設計，而非動作
2. **無狀態**: 每個請求必須包含處理該請求所需的所有資訊
3. **統一介面**: 使用標準的 HTTP 方法和狀態碼
4. **可快取**: 回應應明確標示是否可被快取
5. **分層架構**: 客戶端無需知道是否直接連接到終端伺服器

### 資源識別
```http
# 正確 - 使用名詞表示資源
GET /api/v1/users
GET /api/v1/users/123
GET /api/v1/users/123/orders

# 錯誤 - 使用動詞
GET /api/v1/getUsers
GET /api/v1/getUserById/123
```

## URL 設計規範

### 命名慣例
```http
# 基本格式
/api/v{版本號}/{資源名稱}

# 資源集合
GET /api/v1/users                    # 取得所有使用者
POST /api/v1/users                   # 建立新使用者

# 特定資源
GET /api/v1/users/{id}               # 取得特定使用者
PUT /api/v1/users/{id}               # 更新特定使用者
DELETE /api/v1/users/{id}            # 刪除特定使用者

# 巢狀資源
GET /api/v1/users/{id}/orders        # 取得使用者的訂單
POST /api/v1/users/{id}/orders       # 為使用者建立訂單
GET /api/v1/users/{id}/orders/{order_id}  # 取得特定訂單
```

### 查詢參數
```http
# 分頁
GET /api/v1/users?page=1&limit=20
GET /api/v1/users?offset=0&limit=20

# 排序
GET /api/v1/users?sort=created_at&order=desc
GET /api/v1/users?sort=name,email&order=asc

# 篩選
GET /api/v1/users?status=active
GET /api/v1/users?created_after=2024-01-01
GET /api/v1/users?search=john

# 欄位選擇
GET /api/v1/users?fields=id,name,email
GET /api/v1/users/{id}?include=profile,orders
```

## HTTP 方法使用

### 標準方法對應
```http
# GET - 讀取資源 (安全且冪等)
GET /api/v1/users                    # 取得使用者列表
GET /api/v1/users/{id}               # 取得特定使用者

# POST - 建立資源 (非冪等)
POST /api/v1/users                   # 建立新使用者
POST /api/v1/users/{id}/orders       # 為使用者建立訂單

# PUT - 完整更新資源 (冪等)
PUT /api/v1/users/{id}               # 完整更新使用者資料

# PATCH - 部分更新資源 (冪等)
PATCH /api/v1/users/{id}             # 部分更新使用者資料

# DELETE - 刪除資源 (冪等)
DELETE /api/v1/users/{id}            # 刪除使用者
```

### 非標準動作
```http
# 使用 POST 處理非 CRUD 操作
POST /api/v1/users/{id}/activate     # 啟用使用者
POST /api/v1/users/{id}/reset-password  # 重置密碼
POST /api/v1/orders/{id}/cancel      # 取消訂單
POST /api/v1/payments/{id}/refund    # 退款
```

## 請求/回應格式

### 請求格式

#### Content-Type 標頭
```http
# JSON 請求
Content-Type: application/json

# 檔案上傳
Content-Type: multipart/form-data

# 表單提交
Content-Type: application/x-www-form-urlencoded
```

#### 請求範例
```json
// POST /api/v1/users
{
  "username": "john_doe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "profile": {
    "phone": "+1234567890",
    "address": {
      "street": "123 Main St",
      "city": "New York",
      "country": "US"
    }
  }
}
```

### 回應格式

#### 成功回應
```json
// 單一資源回應
{
  "success": true,
  "data": {
    "id": 123,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "message": "User retrieved successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}

// 列表回應 (含分頁)
{
  "success": true,
  "data": [
    {
      "id": 123,
      "username": "john_doe",
      "email": "john@example.com"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  },
  "message": "Users retrieved successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 空結果回應
```json
// 無資料時
{
  "success": true,
  "data": [],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 0,
    "total_pages": 0,
    "has_next": false,
    "has_prev": false
  },
  "message": "No users found",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 狀態碼規範

### 成功回應 (2xx)
```http
200 OK                    # 成功回應 (GET, PUT, PATCH)
201 Created              # 資源建立成功 (POST)
202 Accepted             # 請求已接受，但尚未處理完成
204 No Content           # 成功但無回應內容 (DELETE)
```

### 客戶端錯誤 (4xx)
```http
400 Bad Request          # 請求格式錯誤
401 Unauthorized         # 未認證
403 Forbidden            # 已認證但無權限
404 Not Found            # 資源不存在
405 Method Not Allowed   # HTTP 方法不被允許
409 Conflict             # 資源衝突 (如重複建立)
422 Unprocessable Entity # 請求格式正確但語義錯誤
429 Too Many Requests    # 請求頻率過高
```

### 伺服器錯誤 (5xx)
```http
500 Internal Server Error  # 伺服器內部錯誤
502 Bad Gateway           # 上游伺服器錯誤
503 Service Unavailable   # 服務暫時不可用
504 Gateway Timeout       # 上游伺服器逾時
```

## 錯誤處理

### 錯誤回應格式
```json
// 基本錯誤格式
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Email format is invalid"
      },
      {
        "field": "password",
        "message": "Password must be at least 8 characters"
      }
    ]
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/v1/users",
  "request_id": "req_123456789"
}

// 單一錯誤
{
  "success": false,
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User with ID 123 not found"
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/v1/users/123",
  "request_id": "req_123456789"
}
```

### 錯誤代碼規範
```json
// 認證相關錯誤
{
  "INVALID_CREDENTIALS": "Invalid username or password",
  "TOKEN_EXPIRED": "Authentication token has expired",
  "TOKEN_INVALID": "Invalid authentication token",
  "INSUFFICIENT_PERMISSIONS": "Insufficient permissions to access this resource"
}

// 驗證相關錯誤
{
  "VALIDATION_ERROR": "Request validation failed",
  "REQUIRED_FIELD_MISSING": "Required field is missing",
  "INVALID_FORMAT": "Field format is invalid",
  "VALUE_OUT_OF_RANGE": "Field value is out of allowed range"
}

// 業務邏輯錯誤
{
  "RESOURCE_NOT_FOUND": "Requested resource not found",
  "RESOURCE_ALREADY_EXISTS": "Resource already exists",
  "OPERATION_NOT_ALLOWED": "Operation not allowed in current state",
  "INSUFFICIENT_BALANCE": "Insufficient account balance"
}
```

## 版本控管

### URL 版本控制
```http
# 推薦方式 - URL 路徑版本
GET /api/v1/users
GET /api/v2/users

# 查詢參數版本 (備選)
GET /api/users?version=1
GET /api/users?v=2
```

### 標頭版本控制
```http
# Accept 標頭版本控制
GET /api/users
Accept: application/vnd.api+json;version=1

# 自訂標頭版本控制
GET /api/users
API-Version: 1
```

### 版本相容性
```json
// v1 回應
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com"
}

// v2 回應 (向後相容)
{
  "id": 123,
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",  // 新增欄位
  "email": "john@example.com",
  "name": "John Doe"        // 保留舊欄位以相容 v1
}
```

## 認證與授權

### JWT 認證
```http
# 登入請求
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "secure_password"
}

# 登入回應
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": 123,
      "username": "john_doe",
      "email": "john@example.com"
    }
  }
}

# 使用 token 進行 API 呼叫
GET /api/v1/users/profile
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 權限檢查
```http
# 角色基礎權限 (RBAC)
GET /api/v1/admin/users
Authorization: Bearer <admin_token>

# 資源擁有者權限
GET /api/v1/users/123/orders
Authorization: Bearer <user_123_token>

# 權限不足回應
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "message": "You don't have permission to access this resource"
  }
}
```

## API 文檔

### OpenAPI/Swagger 規範

#### FastAPI 自動文檔
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
    title="Enterprise API",
    description="企業內部系統 API 文檔",
    version="1.0.0",
    contact={
        "name": "API 支援團隊",
        "email": "api-support@company.com"
    }
)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

    class Config:
        schema_extra = {
            "example": {
                "id": 123,
                "username": "john_doe",
                "email": "john@example.com",
                "is_active": True
            }
        }

@app.get(
    "/api/v1/users/{user_id}",
    response_model=UserResponse,
    summary="取得使用者資料",
    description="根據使用者 ID 取得使用者詳細資料",
    responses={
        200: {"description": "成功回應"},
        404: {"description": "使用者不存在"},
        401: {"description": "未認證"}
    },
    tags=["使用者管理"]
)
async def get_user(user_id: int):
    """
    取得特定使用者的詳細資料。

    - **user_id**: 使用者的唯一識別碼

    回應包含使用者的基本資訊，包括 ID、使用者名稱、Email 和狀態。
    """
    # API 實作...
    pass
```

### API 文檔最佳實踐

#### 完整的端點描述
```yaml
# openapi.yaml
paths:
  /api/v1/users:
    get:
      summary: 取得使用者列表
      description: |
        取得系統中所有使用者的列表，支援分頁和篩選功能。

        ### 功能特色
        - 支援分頁查詢
        - 支援多欄位搜尋
        - 支援狀態篩選
        - 支援排序

        ### 使用範例
        ```
        GET /api/v1/users?page=1&limit=20&search=john&status=active
        ```
      parameters:
        - name: page
          in: query
          description: 頁碼 (從 1 開始)
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: limit
          in: query
          description: 每頁筆數
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
      responses:
        '200':
          description: 成功回應
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserListResponse'
              examples:
                success:
                  summary: 成功範例
                  value:
                    success: true
                    data: [
                      {
                        "id": 1,
                        "username": "john_doe",
                        "email": "john@example.com"
                      }
                    ]
```

### 測試與範例

#### API 測試範例
```python
# tests/test_user_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_users_success():
    """測試成功取得使用者列表"""
    response = client.get("/api/v1/users")

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "data" in data
    assert "pagination" in data
    assert isinstance(data["data"], list)

def test_get_user_by_id_not_found():
    """測試取得不存在的使用者"""
    response = client.get("/api/v1/users/999999")

    assert response.status_code == 404
    data = response.json()

    assert data["success"] is False
    assert data["error"]["code"] == "USER_NOT_FOUND"

def test_create_user_validation_error():
    """測試建立使用者時的驗證錯誤"""
    invalid_user = {
        "username": "",  # 空的使用者名稱
        "email": "invalid-email"  # 無效的 Email 格式
    }

    response = client.post("/api/v1/users", json=invalid_user)

    assert response.status_code == 422
    data = response.json()

    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert len(data["error"]["details"]) >= 2
```

### 變更日誌

#### API 變更追蹤
```markdown
# API 變更日誌

## v2.0.0 (2024-02-01)

### 重大變更 (Breaking Changes)
- **用戶資料結構調整**: `name` 欄位分拆為 `first_name` 和 `last_name`
- **認證方式更新**: 改用 JWT token 取代 session cookie

### 新增功能
- 新增使用者頭像上傳 API: `POST /api/v2/users/{id}/avatar`
- 支援批次使用者操作: `POST /api/v2/users/batch`

### 改進項目
- 優化搜尋效能，新增全文檢索支援
- 改善錯誤訊息，提供更詳細的驗證資訊

### 棄用項目
- `GET /api/v1/users/search` 即將在 v3.0.0 移除，請使用 `GET /api/v2/users?search=` 替代

## v1.2.0 (2024-01-15)

### 新增功能
- 新增使用者狀態管理 API
- 支援使用者匯出功能

### 修正問題
- 修正分頁邊界條件錯誤
- 修正排序參數驗證問題
```

---

*最後更新: 2025-01-XX*
