# API 設計規範

## 🌐 RESTful API 設計原則

### URL 設計規範

#### 資源命名

- 使用名詞，避免動詞
- 使用複數形式：`/users`, `/orders`
- 使用小寫字母和連字符：`/user-profiles`

#### URL 結構

```
# 基本結構
/api/v1/{resource}
/api/v1/{resource}/{id}
/api/v1/{resource}/{id}/{sub-resource}

# 範例
GET    /api/v1/users                    # 獲取用戶列表
POST   /api/v1/users                    # 創建用戶
GET    /api/v1/users/123                # 獲取特定用戶
PUT    /api/v1/users/123                # 更新用戶
DELETE /api/v1/users/123                # 刪除用戶
GET    /api/v1/users/123/orders         # 獲取用戶的訂單
```

### HTTP 方法使用

| 方法   | 用途          | 冪等性 | 安全性 |
| ------ | ------------- | ------ | ------ |
| GET    | 獲取資源      | ✅     | ✅     |
| POST   | 創建資源      | ❌     | ❌     |
| PUT    | 更新/替換資源 | ✅     | ❌     |
| PATCH  | 部分更新資源  | ❌     | ❌     |
| DELETE | 刪除資源      | ✅     | ❌     |

### HTTP 狀態碼規範

#### 成功響應 (2xx)

- `200 OK` - 請求成功
- `201 Created` - 資源創建成功
- `204 No Content` - 請求成功但無內容返回

#### 客戶端錯誤 (4xx)

- `400 Bad Request` - 請求格式錯誤
- `401 Unauthorized` - 未認證
- `403 Forbidden` - 無權限
- `404 Not Found` - 資源不存在
- `409 Conflict` - 資源衝突
- `422 Unprocessable Entity` - 驗證失敗

#### 服務器錯誤 (5xx)

- `500 Internal Server Error` - 服務器內部錯誤
- `502 Bad Gateway` - 網關錯誤
- `503 Service Unavailable` - 服務不可用

## 📝 請求與響應格式

### 請求格式

#### 查詢參數

```python
# 分頁
GET /api/v1/users?page=1&size=20

# 排序
GET /api/v1/users?sort=created_at&order=desc

# 篩選
GET /api/v1/users?status=active&role=admin

# 搜尋
GET /api/v1/users?search=john&fields=username,email
```

#### 請求體 (JSON)

```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true
}
```

### 響應格式

#### 成功響應

```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "message": "User created successfully"
}
```

#### 列表響應 (分頁)

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 100,
      "pages": 5
    }
  }
}
```

#### 錯誤響應

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "email": ["Email is required"],
      "username": ["Username must be at least 3 characters"]
    }
  },
  "request_id": "req_123456789"
}
```

## 🔧 FastAPI 實作規範

### 路由組織

```python
# api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from core.database import get_db
from services.user_service import UserService
from models.schemas.user import User, UserCreate, UserUpdate
from models.schemas.common import PaginatedResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=PaginatedResponse[User])
async def get_users(
    page: int = Query(1, ge=1, description="頁碼"),
    size: int = Query(20, ge=1, le=100, description="每頁數量"),
    search: Optional[str] = Query(None, description="搜尋關鍵字"),
    status: Optional[str] = Query(None, description="用戶狀態"),
    db: AsyncSession = Depends(get_db)
):
    """
    獲取用戶列表

    - **page**: 頁碼 (從 1 開始)
    - **size**: 每頁數量 (1-100)
    - **search**: 搜尋用戶名或郵箱
    - **status**: 篩選用戶狀態 (active/inactive)
    """
    user_service = UserService(db)
    return await user_service.get_users_paginated(
        page=page,
        size=size,
        search=search,
        status=status
    )

@router.post("/", response_model=User, status_code=201)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """創建新用戶"""
    user_service = UserService(db)
    try:
        return await user_service.create_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """獲取特定用戶"""
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新用戶資訊"""
    user_service = UserService(db)
    user = await user_service.update_user(user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """刪除用戶"""
    user_service = UserService(db)
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
```

### 資料驗證模型

```python
# models/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用戶名")
    email: EmailStr = Field(..., description="郵箱地址")
    first_name: Optional[str] = Field(None, max_length=100, description="名字")
    last_name: Optional[str] = Field(None, max_length=100, description="姓氏")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="密碼")

    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('密碼必須包含至少一個大寫字母')
        if not any(c.islower() for c in v):
            raise ValueError('密碼必須包含至少一個小寫字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密碼必須包含至少一個數字')
        return v

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# models/schemas/common.py
from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar('T')

class PaginationInfo(BaseModel):
    page: int
    size: int
    total: int
    pages: int

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    pagination: PaginationInfo
```

### 異常處理

```python
# core/exceptions.py
from fastapi import HTTPException

class BaseAPIException(HTTPException):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)

class ValidationError(BaseAPIException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=422)

class NotFoundError(BaseAPIException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(detail=f"{resource} not found", status_code=404)

class ConflictError(BaseAPIException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=409)

class UnauthorizedError(BaseAPIException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(detail=detail, status_code=401)

# 全局異常處理器
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(BaseAPIException)
async def api_exception_handler(request: Request, exc: BaseAPIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.__class__.__name__.upper(),
                "message": exc.detail
            },
            "request_id": getattr(request.state, "request_id", None)
        }
    )
```

## 🔐 認證與授權

### JWT 認證

```python
# core/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user
```

### 權限控制

```python
# core/permissions.py
from functools import wraps
from fastapi import HTTPException, status

def require_permissions(*required_permissions):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            user_permissions = await get_user_permissions(current_user.id)
            if not all(perm in user_permissions for perm in required_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 使用範例
@router.delete("/{user_id}")
@require_permissions("user:delete")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    pass
```

## 📊 API 文檔

### OpenAPI 配置

```python
# main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="My API",
    description="A comprehensive API for user management",
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        description="A comprehensive API for user management",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### API 文檔註解

```python
@router.post("/", response_model=User, status_code=201)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    創建新用戶

    創建一個新的用戶帳戶。郵箱地址必須是唯一的。

    - **username**: 用戶名 (3-50 字符)
    - **email**: 郵箱地址 (必須是有效的郵箱格式)
    - **password**: 密碼 (至少 8 字符，包含大小寫字母和數字)
    - **first_name**: 名字 (可選)
    - **last_name**: 姓氏 (可選)

    Returns:
        User: 創建的用戶資訊 (不包含密碼)

    Raises:
        400: 郵箱已存在或驗證失敗
        422: 請求資料格式錯誤
    """
    pass
```

## 🧪 API 測試

### 單元測試

```python
# tests/test_users_api.py
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123",
        "first_name": "Test",
        "last_name": "User"
    }

    response = await client.post("/api/v1/users/", json=user_data)

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "password" not in data  # 確保密碼不會返回

@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient):
    response = await client.get("/api/v1/users/999")

    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "not found" in data["error"]["message"].lower()
```

## 📈 API 監控

### 請求日誌

```python
# middleware/logging.py
import time
import logging
from fastapi import Request

logger = logging.getLogger("api")

async def log_requests(request: Request, call_next):
    start_time = time.time()

    # 記錄請求
    logger.info(
        f"API Request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host
        }
    )

    response = await call_next(request)

    # 記錄響應
    process_time = time.time() - start_time
    logger.info(
        f"API Response: {response.status_code} in {process_time:.4f}s",
        extra={
            "status_code": response.status_code,
            "process_time": process_time
        }
    )

    return response
```

### 性能監控

```python
# middleware/metrics.py
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response

@app.get("/metrics")
async def get_metrics():
    return Response(generate_latest(), media_type="text/plain")
```
