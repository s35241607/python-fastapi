# 後端開發規範

## 🏗️ 三層式架構

### 架構層級

```
backend/
├── app/
│   ├── api/           # API 層 (Presentation Layer)
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   └── dependencies.py
│   │   └── __init__.py
│   ├── core/          # 核心配置
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── middleware.py
│   ├── services/      # 業務邏輯層 (Business Logic Layer)
│   │   ├── user_service.py
│   │   ├── auth_service.py
│   │   └── __init__.py
│   ├── repositories/  # 資料存取層 (Data Access Layer)
│   │   ├── user_repository.py
│   │   ├── base_repository.py
│   │   └── __init__.py
│   ├── models/        # 資料模型
│   │   ├── database/  # SQLAlchemy 模型
│   │   ├── schemas/   # Pydantic 模型
│   │   └── __init__.py
│   ├── utils/         # 工具函數
│   └── main.py
```

## 📝 命名規則

### 檔案命名

- 使用 snake_case：`user_service.py`
- 模組名稱要有意義：`email_validator.py`

### 類別命名

- 使用 PascalCase：`UserService`, `DatabaseConnection`
- 抽象類別加 `Abstract` 前綴：`AbstractRepository`

### 函數命名

- 使用 snake_case：`get_user_by_id`, `create_new_user`
- 異步函數使用 `async def` 關鍵字，並遵循 `snake_case` 命名：`async def fetch_users_async()`

### 變數命名

- 使用 snake_case：`user_id`, `email_address`
- 常數使用 UPPER_CASE：`MAX_CONNECTIONS`, `DEFAULT_TIMEOUT`

### API 端點命名

- 使用複數名詞：`/users/`, `/orders/`
- RESTful 風格：
  ```python
  GET    /api/v1/users/           # 獲取用戶列表
  POST   /api/v1/users/           # 創建用戶
  GET    /api/v1/users/{id}/      # 獲取特定用戶
  PUT    /api/v1/users/{id}/      # 更新用戶
  DELETE /api/v1/users/{id}/      # 刪除用戶
  ```

## ⚡ 異步開發規範

### 1. 所有 I/O 操作必須使用 async/await

```python
# ✅ 正確
async def get_user_by_id(user_id: int) -> Optional[User]:
    async with get_db_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

# ❌ 錯誤
def get_user_by_id(user_id: int) -> Optional[User]:
    session = get_db_session()
    return session.query(User).filter(User.id == user_id).first()
```

### 2. 資料庫操作

```python
# ✅ 使用異步 SQLAlchemy
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload

async def get_user_with_items(user_id: int, session: AsyncSession) -> Optional[User]:
    result = await session.execute(
        select(User)
        .options(selectinload(User.items))
        .where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```

### 3. HTTP 請求

```python
# ✅ 使用 httpx 進行異步 HTTP 請求
import httpx

async def call_external_api(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

## 🔗 資料庫連線池配置

### 1. 異步資料庫引擎設定

```python
# core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

engine = create_async_engine(
    DATABASE_URL,
    # 連線池設定
    pool_size=20,           # 連線池大小
    max_overflow=30,        # 最大溢出連線數
    pool_pre_ping=True,     # 連線前檢查
    pool_recycle=3600,      # 連線回收時間 (秒)
    echo=False,             # 生產環境設為 False
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### 2. 連線池監控

```python
# utils/db_monitor.py
import logging
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    logger.info("Database connection established")

@event.listens_for(Engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    logger.debug("Connection checked out from pool")

@event.listens_for(Engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    logger.debug("Connection checked in to pool")
```

## 🛡️ Middleware 規範

### 1. 錯誤處理 Middleware

```python
# core/middleware.py
import logging
import traceback
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.error(
                f"Unhandled exception: {exc}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "traceback": traceback.format_exc()
                }
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    "request_id": getattr(request.state, "request_id", None)
                }
            )
```

### 2. 日誌 Middleware

```python
import time
import uuid
from fastapi import Request

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 生成請求 ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 記錄請求開始
        start_time = time.time()
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host
            }
        )

        # 處理請求
        response = await call_next(request)

        # 記錄請求結束
        process_time = time.time() - start_time
        logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": f"{process_time:.4f}s"
            }
        )

        response.headers["X-Request-ID"] = request_id
        return response
```

### 3. CORS Middleware

```python
from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"]
    )
```

## 🏛️ Repository 模式

### 1. 基礎 Repository

```python
# repositories/base_repository.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

T = TypeVar('T')

class BaseRepository(Generic[T], ABC):
    def __init__(self, session: AsyncSession, model_class: type[T]):
        self.session = session
        self.model_class = model_class

    async def get_by_id(self, id: int) -> Optional[T]:
        result = await self.session.execute(
            select(self.model_class).where(self.model_class.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        result = await self.session.execute(
            select(self.model_class).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, obj: T) -> T:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, id: int, **kwargs) -> Optional[T]:
        await self.session.execute(
            update(self.model_class)
            .where(self.model_class.id == id)
            .values(**kwargs)
        )
        return await self.get_by_id(id)

    async def delete(self, id: int) -> bool:
        result = await self.session.execute(
            delete(self.model_class).where(self.model_class.id == id)
        )
        return result.rowcount > 0
```

### 2. 具體 Repository

```python
# repositories/user_repository.py
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.database.user import User
from repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_active_users(self) -> List[User]:
        result = await self.session.execute(
            select(User).where(User.is_active == True)
        )
        return result.scalars().all()
```

## 🔧 Service 層規範

```python
# services/user_service.py
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.user_repository import UserRepository
from models.schemas.user import UserCreate, UserUpdate
from models.database.user import User
from core.security import get_password_hash

class UserService:
    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)

    async def create_user(self, user_data: UserCreate) -> User:
        # 檢查用戶是否已存在
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # 創建新用戶
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password
        )

        return await self.user_repo.create(user)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        return await self.user_repo.get_by_id(user_id)

    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        return await self.user_repo.update(user_id, **user_data.dict(exclude_unset=True))
```

## 📊 日誌配置

```python
# core/logging.py
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logging():
    # 創建 logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 創建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件處理器
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
```

## ✅ Clean Code 原則

### 1. 函數設計

- 單一職責原則
- 函數名稱要清楚表達意圖
- 參數不超過 3 個，使用 dataclass 或 Pydantic 模型

### 2. 錯誤處理

```python
# ✅ 使用自定義異常
class UserNotFoundError(Exception):
    pass

class EmailAlreadyExistsError(Exception):
    pass

# ✅ 在 service 層處理業務邏輯錯誤
async def create_user(self, user_data: UserCreate) -> User:
    if await self.user_repo.get_by_email(user_data.email):
        raise EmailAlreadyExistsError(f"Email {user_data.email} already exists")
```

### 3. 類型提示

```python
from typing import Optional, List, Dict, Any

async def get_users(
    skip: int = 0,
    limit: int = 100,
    filters: Optional[Dict[str, Any]] = None
) -> List[User]:
    pass
```

### 4. 文檔字串

```python
async def create_user(self, user_data: UserCreate) -> User:
    """
    創建新用戶

    Args:
        user_data: 用戶創建資料

    Returns:
        User: 創建的用戶物件

    Raises:
        EmailAlreadyExistsError: 當 email 已存在時
    """
    pass
```
